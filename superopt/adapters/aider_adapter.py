"""
Aider Adapter for SuperOpt

Integrates SuperOpt with the Aider coding agent framework.

Aider is licensed under the Apache License 2.0.
Copyright Aider AI contributors

See: https://github.com/Aider-AI/aider
"""

import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from superopt.adapters.base import AgentAdapter
from superopt.core.environment import (
    AgenticEnvironment,
    PromptConfig,
    RetrievalConfig,
    ToolSchema,
)
from superopt.core.trace import (
    ExecutionTrace,
    FailureType,
    ToolCall,
)


class TraceCapturingIO:
    """
    Custom IO class that captures all Aider output for trace building.

    This class wraps Aider's InputOutput to capture:
    - Tool calls (file edits, commands)
    - Tool errors and warnings
    - Model outputs
    - File operations
    """

    def __init__(self, trace: ExecutionTrace, pretty: bool = False, yes: bool = True):
        self.trace = trace
        self.pretty = pretty
        self.yes = yes

        # Capture buffers
        self.tool_outputs: list[str] = []
        self.tool_errors: list[str] = []
        self.tool_warnings: list[str] = []
        self.file_edits: list[dict[str, Any]] = []
        self.commands_run: list[str] = []

        # Required attributes for Aider compatibility
        self.encoding = "utf-8"
        self.dry_run = False
        self.never_prompts = set()
        self.num_error_outputs = 0
        self.num_user_asks = 0
        self.multiline_mode = False
        self.placeholder = None
        self.input_history_file = None
        self.chat_history_file = None
        self.llm_history_file = None
        self.root = "."

    def tool_output(self, *messages, log_only=False, bold=False):
        """Capture tool output."""
        msg = " ".join(str(m) for m in messages) if messages else ""
        self.tool_outputs.append(msg)

        # Detect file edit patterns
        if "Applied edit to" in msg:
            match = re.search(r"Applied edit to (.+)", msg)
            if match:
                self.file_edits.append({"file": match.group(1), "action": "edit", "success": True})
                self.trace.tool_calls.append(
                    ToolCall(
                        tool_name="edit_file",
                        arguments={"file": match.group(1)},
                        success=True,
                    )
                )

    def tool_error(self, message="", strip=True):
        """Capture tool errors."""
        self.num_error_outputs += 1
        self.tool_errors.append(str(message))

        # Add to trace
        self.trace.tool_errors.append(
            ToolCall(
                tool_name="unknown",
                arguments={},
                success=False,
                error_message=str(message),
            )
        )

        # Detect specific error types
        msg_lower = message.lower() if message else ""
        if any(kw in msg_lower for kw in ["syntax", "nameerror", "typeerror", "importerror"]):
            self.trace.compiler_errors.append(str(message))

    def tool_warning(self, message="", strip=True):
        """Capture tool warnings."""
        self.tool_warnings.append(str(message))

    def user_input(self, inp, log_only=True):
        """Handle user input logging."""
        pass

    def ai_output(self, content):
        """Handle AI output."""
        if content:
            self.trace.model_outputs.append(content)

    def assistant_output(self, message, pretty=None):
        """Handle assistant output."""
        if message:
            self.trace.model_outputs.append(message)

    def confirm_ask(
        self,
        question,
        default="y",
        subject=None,
        explicit_yes_required=False,
        group=None,
        allow_never=False,
    ):
        """Auto-confirm all prompts for non-interactive execution."""
        self.num_user_asks += 1
        return not explicit_yes_required  # Yes unless explicit yes required

    def prompt_ask(self, question, default="", subject=None):
        """Auto-respond to prompts."""
        self.num_user_asks += 1
        return default

    def get_input(self, *args, **kwargs):
        """Not used in non-interactive mode."""
        raise EOFError("Non-interactive mode")

    def read_text(self, filename, silent=False):
        """Read file content."""
        try:
            with open(str(filename), encoding=self.encoding) as f:
                return f.read()
        except (FileNotFoundError, IsADirectoryError, UnicodeError) as e:
            if not silent:
                self.tool_error(f"{filename}: {e}")
            return None

    def write_text(self, filename, content):
        """Write file content."""
        if self.dry_run:
            return
        try:
            with open(str(filename), "w", encoding=self.encoding) as f:
                f.write(content)
            self.file_edits.append({"file": str(filename), "action": "write", "success": True})
        except OSError as e:
            self.tool_error(f"Unable to write file {filename}: {e}")

    def get_assistant_mdstream(self):
        """Return a dummy markdown stream."""
        return None

    def llm_started(self):
        """Mark LLM processing started."""
        pass

    def rule(self):
        """Print separator (no-op for capture)."""
        pass

    def append_chat_history(self, text, linebreak=False, blockquote=False, strip=True):
        """Append to chat history (no-op for capture)."""
        pass

    def add_to_input_history(self, inp):
        """Add to input history (no-op for capture)."""
        pass

    def log_llm_history(self, role, content):
        """Log LLM history (no-op for capture)."""
        pass

    def offer_url(self, url, prompt="Open URL?", allow_never=True):
        """Never open URLs in non-interactive mode."""
        return False


class AiderAdapter(AgentAdapter):
    """
    Adapter for integrating Aider with SuperOpt.

    This adapter allows SuperOpt to:
    - Execute coding tasks via Aider (library or subprocess)
    - Capture detailed execution traces
    - Apply environment updates to modify Aider's behavior

    Supports two execution modes:
    1. Library mode: Direct Python API integration (faster, more detailed traces)
    2. Subprocess mode: CLI invocation fallback (works without library install)
    """

    def __init__(
        self,
        workspace_dir: Path | None = None,
        model_name: str | None = None,
        use_subprocess: bool = False,
    ):
        """
        Initialize Aider adapter.

        Args:
            workspace_dir: Directory for Aider to work in
            model_name: Model name for Aider (e.g., "ollama/llama3.1:8b")
            use_subprocess: Force subprocess mode even if library is available
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.model_name = model_name or "ollama/llama3.1:8b"
        self.use_subprocess = use_subprocess
        self._trace_buffer: list[ExecutionTrace] = []
        self._temp_workspace: Path | None = None
        self._current_environment: AgenticEnvironment | None = None
        self._aider_available = self._check_aider_available()

    def _check_aider_available(self) -> bool:
        """Check if Aider is available as a library."""
        if self.use_subprocess:
            return False
        try:
            # Check if aider is installed as a package
            from aider.coders import Coder  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_workspace_dir(self) -> Path:
        """Get or create workspace directory."""
        if self.workspace_dir:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            return self.workspace_dir

        if not self._temp_workspace:
            self._temp_workspace = Path(tempfile.mkdtemp(prefix="superopt_aider_"))

        return self._temp_workspace

    def _init_git_repo(self, workspace: Path):
        """Initialize git repo in workspace if needed."""
        git_dir = workspace / ".git"
        if not git_dir.exists():
            import subprocess

            subprocess.run(["git", "init"], cwd=workspace, capture_output=True, check=False)
            # Configure git user for commits
            subprocess.run(
                ["git", "config", "user.email", "superopt@test.local"],
                cwd=workspace,
                capture_output=True,
                check=False,
            )
            subprocess.run(
                ["git", "config", "user.name", "SuperOpt"],
                cwd=workspace,
                capture_output=True,
                check=False,
            )

    def execute(
        self,
        task_description: str,
        environment: AgenticEnvironment,
    ) -> ExecutionTrace:
        """
        Execute Aider with given environment and capture trace.

        Args:
            task_description: Coding task description
            environment: Environment configuration

        Returns:
            ExecutionTrace with real execution data
        """
        self._current_environment = environment
        workspace = self._get_workspace_dir()
        self._init_git_repo(workspace)

        # Create trace
        trace = ExecutionTrace(
            task_description=task_description,
            task_id=f"aider_{datetime.now().timestamp()}",
            prompt_snapshot=environment.prompts.to_dict(),
            success=False,
            timestamp=datetime.now(),
        )

        start_time = datetime.now()

        if self._aider_available:
            self._execute_library_mode(task_description, environment, trace, workspace)
        else:
            self._execute_subprocess_mode(task_description, environment, trace, workspace)

        # Calculate duration
        trace.duration_seconds = (datetime.now() - start_time).total_seconds()

        # Determine failure type based on trace contents
        trace.failure_type = self._classify_failure(trace)

        self._trace_buffer.append(trace)
        return trace

    def _execute_library_mode(
        self,
        task_description: str,
        environment: AgenticEnvironment,
        trace: ExecutionTrace,
        workspace: Path,
    ):
        """Execute using Aider as a Python library."""
        try:
            from aider.coders import Coder
            from aider.models import Model

            # Create our trace-capturing IO
            capturing_io = TraceCapturingIO(trace)
            capturing_io.root = str(workspace)

            # Create model
            model = Model(self.model_name)

            # Create Coder instance with our custom IO
            coder = Coder.create(
                main_model=model,
                io=capturing_io,
                fnames=[],
                use_git=True,
                stream=False,
                auto_commits=False,
            )

            # Apply environment: add tool constraints to system prompt
            self._apply_tool_constraints(coder, environment)

            # Execute task
            coder.run(with_message=task_description)

            # Check success based on captured data
            if capturing_io.file_edits and not capturing_io.tool_errors:
                trace.success = True

            # Get response content
            if hasattr(coder, "partial_response_content") and coder.partial_response_content:
                trace.model_outputs.append(coder.partial_response_content)

        except Exception as e:
            trace.runtime_exceptions.append(str(e))
            trace.failure_message = f"Library execution failed: {e}"

    def _execute_subprocess_mode(
        self,
        task_description: str,
        environment: AgenticEnvironment,
        trace: ExecutionTrace,
        workspace: Path,
    ):
        """Execute Aider as a subprocess (fallback mode)."""
        import subprocess

        # Build command
        cmd = [
            "aider",
            "--model",
            self.model_name,
            "--yes",  # Auto-confirm
            "--no-auto-commits",
            "--no-git",  # We manage git ourselves
            "--message",
            task_description,
        ]

        # Add any files in workspace
        for f in workspace.glob("*.py"):
            cmd.append(str(f.relative_to(workspace)))

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse output
            stdout = result.stdout
            stderr = result.stderr

            trace.model_outputs.append(stdout)

            # Detect errors
            if result.returncode != 0:
                trace.failure_message = f"Exit code {result.returncode}"
                if stderr:
                    trace.tool_errors.append(
                        ToolCall(
                            tool_name="aider_cli",
                            arguments={"command": " ".join(cmd)},
                            success=False,
                            error_message=stderr[:500],
                        )
                    )
            else:
                # Check for file modifications
                if "Applied edit" in stdout or "Wrote" in stdout:
                    trace.success = True
                    # Extract file edits
                    for match in re.finditer(r"Applied edit to (.+)", stdout):
                        trace.tool_calls.append(
                            ToolCall(
                                tool_name="edit_file",
                                arguments={"file": match.group(1)},
                                success=True,
                            )
                        )

            # Detect specific error patterns
            for pattern, error_type in [
                (r"SyntaxError", "syntax"),
                (r"NameError", "name"),
                (r"TypeError", "type"),
                (r"ImportError", "import"),
            ]:
                if re.search(pattern, stdout + stderr):
                    trace.compiler_errors.append(f"{error_type} error detected")

        except subprocess.TimeoutExpired:
            trace.failure_message = "Execution timed out (300s)"
            trace.runtime_exceptions.append("TimeoutExpired")
        except FileNotFoundError:
            trace.failure_message = "aider command not found"
            trace.runtime_exceptions.append("aider CLI not installed")
        except Exception as e:
            trace.failure_message = str(e)
            trace.runtime_exceptions.append(str(e))

    def _apply_tool_constraints(self, coder, environment: AgenticEnvironment):
        """Apply tool constraints from environment to coder."""
        # Aider doesn't have a direct tool schema API, so we inject constraints
        # into the system prompt or coder's gpt_prompts
        if not environment.tools:
            return

        constraints = []
        for tool_name, schema in environment.tools.items():
            if schema.constraints:
                for constraint in schema.constraints:
                    constraints.append(f"- {tool_name}: {constraint}")

        if constraints and hasattr(coder, "gpt_prompts"):
            extra_rules = "\n\nTOOL CONSTRAINTS:\n" + "\n".join(constraints)
            if hasattr(coder.gpt_prompts, "main_system"):
                coder.gpt_prompts.main_system += extra_rules

    def _classify_failure(self, trace: ExecutionTrace) -> FailureType:
        """Classify the failure type based on trace contents."""
        if trace.success:
            return FailureType.NONE

        # Check for tool errors (schema violations, invalid args)
        if trace.tool_errors:
            for err in trace.tool_errors:
                if err.error_message:
                    msg = err.error_message.lower()
                    if "line" in msg and ("0" in msg or "index" in msg):
                        return FailureType.TOOL  # Line indexing error
                    if "invalid" in msg or "argument" in msg:
                        return FailureType.TOOL
            return FailureType.TOOL

        # Check for retrieval issues (missing symbols, imports)
        if trace.compiler_errors:
            for err in trace.compiler_errors:
                err_lower = err.lower()
                if "not defined" in err_lower or "cannot find" in err_lower:
                    return FailureType.RETRIEVAL
                if "import" in err_lower:
                    return FailureType.RETRIEVAL
            return FailureType.PROMPT  # Other compiler errors = prompt issue

        # Runtime exceptions
        if trace.runtime_exceptions:
            return FailureType.TOOL

        # Default to memory (repeated mistakes, no clear category)
        return FailureType.MEMORY

    def extract_environment(self) -> AgenticEnvironment:
        """Extract current environment configuration."""
        if self._current_environment:
            return self._current_environment

        return AgenticEnvironment(
            prompts=PromptConfig(
                system_prompt="You are a helpful coding assistant.",
            ),
            tools=self._get_default_tool_schemas(),
            retrieval=RetrievalConfig(),
        )

    def apply_environment(self, environment: AgenticEnvironment):
        """Apply environment configuration."""
        self._current_environment = environment

    def get_agent_info(self) -> dict[str, Any]:
        """Get Aider agent information."""
        return {
            "agent_type": "aider",
            "model": self.model_name,
            "mode": "library" if self._aider_available else "subprocess",
            "capabilities": ["file_editing", "code_generation", "refactoring"],
            "workspace": str(self._get_workspace_dir()),
        }

    def _get_default_tool_schemas(self) -> dict[str, ToolSchema]:
        """Get default Aider tool schemas."""
        return {
            "edit_file": ToolSchema(
                name="edit_file",
                description="Edit a file by applying changes. CRITICAL: line_number must be 1-indexed (>= 1).",
                arguments={
                    "file": "str - Relative path to file",
                    "line_number": "int - Line number (1-indexed, must be >= 1)",
                    "changes": "str - The changes to apply",
                },
                required_fields=["file", "changes"],
                constraints=[
                    "line_number must be >= 1 (1-indexed, not 0-indexed)",
                    "File paths must be relative to project root",
                ],
            ),
            "create_file": ToolSchema(
                name="create_file",
                description="Create a new file with content",
                arguments={
                    "file": "str - Relative path to file",
                    "content": "str - File content",
                },
                required_fields=["file", "content"],
                constraints=[],
            ),
            "run_command": ToolSchema(
                name="run_command",
                description="Execute a shell command",
                arguments={
                    "command": "str - Shell command to execute",
                },
                required_fields=["command"],
                constraints=["Never run destructive commands without confirmation"],
            ),
        }

    def get_trace_buffer(self) -> list[ExecutionTrace]:
        """Get all captured traces."""
        return self._trace_buffer.copy()

    def clear_trace_buffer(self):
        """Clear the trace buffer."""
        self._trace_buffer.clear()

    def cleanup(self):
        """Clean up temporary workspace."""
        if self._temp_workspace and self._temp_workspace.exists():
            try:
                shutil.rmtree(self._temp_workspace)
            except Exception:
                pass

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

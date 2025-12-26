"""
Letta Adapter for SuperOpt

Integrates SuperOpt with Letta Code - a memory-first coding agent.
Letta Code uses persistent memory blocks (persona, human, project, skills)
that persist across sessions, making it ideal for demonstrating
memory-related optimizations.
"""

from datetime import datetime
from typing import Any

from superopt.adapters.base import AgentAdapter
from superopt.core.environment import (
    AgenticEnvironment,
    MemoryEntry,
    PromptConfig,
    RetrievalConfig,
    ToolSchema,
)
from superopt.core.trace import (
    ExecutionTrace,
    FailureType,
    MemoryAccess,
)


class LettaAdapter(AgentAdapter):
    """
    Adapter for integrating Letta Code with SuperOpt.

    Letta Code is a memory-first coding agent that:
    - Uses persistent memory blocks (persona, human, project, skills)
    - Maintains state across sessions
    - Learns from previous interactions

    This adapter allows SuperOpt to:
    - Extract memory blocks as MemoryEntry objects
    - Capture memory read/write operations
    - Optimize memory structure and content
    - Demonstrate memory-related benchmarks
    """

    def __init__(self, letta_client=None, agent_id: str | None = None):
        """
        Initialize Letta adapter.

        Args:
            letta_client: Letta Python SDK client instance
            agent_id: Letta agent ID (optional, can be created)
        """
        self.letta_client = letta_client
        self.agent_id = agent_id
        self._trace_buffer: list = []
        self._memory_block_cache: dict[str, str] = {}

    def execute(
        self,
        task_description: str,
        environment: AgenticEnvironment,
    ) -> ExecutionTrace:
        """
        Execute Letta Code agent with given environment and capture trace.

        Args:
            task_description: Coding task description
            environment: Environment configuration

        Returns:
            Execution trace with memory operations
        """
        # Apply environment to Letta agent
        self.apply_environment(environment)

        # Create trace
        trace = ExecutionTrace(
            task_description=task_description,
            task_id=f"letta_{datetime.now().timestamp()}",
            prompt_snapshot=environment.prompts.to_dict(),
            success=False,
        )

        # In a real implementation, we would:
        # 1. Send message to Letta agent
        # 2. Capture tool calls (file edits, commands, etc.)
        # 3. Monitor memory block updates (via Letta SDK)
        # 4. Track memory read/write operations
        # 5. Extract compiler/test results

        if self.letta_client and self.agent_id:
            # Capture memory operations
            self._capture_memory_operations(trace)

            # Execute task and capture tool calls
            # response = self.letta_client.agents.messages.create(
            #     agent_id=self.agent_id,
            #     messages=[{"role": "user", "content": task_description}]
            # )
            #
            # for message in response.messages:
            #     if message.message_type == "tool_call_message":
            #         trace.tool_calls.append(ToolCall(
            #             tool_name=message.tool_call.name,
            #             arguments=message.tool_call.arguments,
            #             success=True,
            #         ))
            #     elif message.message_type == "tool_return_message":
            #         # Check for errors
            #         pass

        # Determine failure type
        if trace.tool_errors:
            trace.failure_type = FailureType.TOOL
        elif trace.memory_reads or trace.memory_writes:
            # Check if memory-related failures occurred
            trace.failure_type = FailureType.MEMORY
        elif trace.success:
            trace.failure_type = FailureType.NONE
        else:
            trace.failure_type = FailureType.MEMORY  # Default for Letta

        self._trace_buffer.append(trace)
        return trace

    def extract_environment(self) -> AgenticEnvironment:
        """
        Extract current environment from Letta agent.

        Returns:
            Current agentic environment with memory blocks
        """
        memory_entries: list[MemoryEntry] = []

        if self.letta_client and self.agent_id:
            # Retrieve memory blocks from Letta
            try:
                blocks = self.letta_client.agents.blocks.list(agent_id=self.agent_id)

                for block in blocks:
                    # Convert Letta memory block to SuperOpt MemoryEntry
                    entry = MemoryEntry(
                        entry_type=self._map_block_label_to_type(block.label),
                        content=block.value,
                        confidence=1.0,  # Letta blocks are persistent
                        timestamp=datetime.now(),
                    )
                    memory_entries.append(entry)
                    self._memory_block_cache[block.label] = block.value
            except Exception:
                # Fallback if client not available
                pass

        return AgenticEnvironment(
            prompts=PromptConfig(
                system_prompt="You are a helpful coding assistant with persistent memory.",
            ),
            tools=self._extract_tool_schemas(),
            retrieval=RetrievalConfig(),
            memory=memory_entries,
        )

    def apply_environment(self, environment: AgenticEnvironment):
        """
        Apply environment configuration to Letta agent.

        Args:
            environment: Environment to apply
        """
        if not (self.letta_client and self.agent_id):
            return

        # Update memory blocks from environment
        for memory_entry in environment.memory:
            block_label = self._map_type_to_block_label(memory_entry.entry_type)

            if block_label:
                try:
                    # Update memory block via Letta SDK
                    self.letta_client.agents.blocks.update(
                        agent_id=self.agent_id,
                        block_label=block_label,
                        value=memory_entry.content,
                    )
                    self._memory_block_cache[block_label] = memory_entry.content
                except Exception:
                    # Block might not exist, create it
                    try:
                        self.letta_client.agents.blocks.create(
                            agent_id=self.agent_id,
                            label=block_label,
                            value=memory_entry.content,
                        )
                    except Exception:
                        pass  # Skip if creation fails

    def get_agent_info(self) -> dict[str, Any]:
        """Get Letta agent information."""
        return {
            "agent_type": "letta_code",
            "version": "unknown",
            "capabilities": [
                "persistent_memory",
                "memory_blocks",
                "file_editing",
                "command_execution",
                "skill_learning",
            ],
            "memory_blocks": list(self._memory_block_cache.keys()),
        }

    def _capture_memory_operations(self, trace: ExecutionTrace):
        """Capture memory read/write operations from Letta agent."""
        if not (self.letta_client and self.agent_id):
            return

        # In a real implementation, we would monitor:
        # - Memory block reads (when agent retrieves blocks)
        # - Memory block writes (when agent updates blocks via tools)
        # - Memory block attachments/detachments

        # For now, simulate based on cache changes
        current_blocks = {}
        try:
            blocks = self.letta_client.agents.blocks.list(agent_id=self.agent_id)
            current_blocks = {b.label: b.value for b in blocks}
        except Exception:
            pass

        # Detect writes (blocks that changed)
        for label, new_value in current_blocks.items():
            old_value = self._memory_block_cache.get(label, "")
            if new_value != old_value:
                trace.memory_writes.append(
                    MemoryAccess(
                        operation="write",
                        entry_type=self._map_block_label_to_type(label),
                        content=new_value,
                    )
                )

        # Detect reads (blocks accessed during execution)
        # This would require hooking into Letta's internal execution
        for label in current_blocks:
            trace.memory_reads.append(
                MemoryAccess(
                    operation="read",
                    entry_type=self._map_block_label_to_type(label),
                )
            )

    def _map_block_label_to_type(self, label: str) -> str:
        """Map Letta block label to SuperOpt memory type."""
        mapping = {
            "persona": "PROMPT_CONSTRAINT",
            "human": "STRATEGY",
            "project": "STRATEGY",
            "skills": "TOOL_RULE",
            "loaded_skills": "TOOL_RULE",
        }
        return mapping.get(label, "STRATEGY")

    def _map_type_to_block_label(self, entry_type: str) -> str | None:
        """Map SuperOpt memory type to Letta block label."""
        reverse_mapping = {
            "PROMPT_CONSTRAINT": "persona",
            "STRATEGY": "project",
            "TOOL_RULE": "skills",
        }
        return reverse_mapping.get(entry_type)

    def _extract_tool_schemas(self) -> dict[str, ToolSchema]:
        """Extract tool schemas from Letta Code."""
        schemas = {
            "edit_file": ToolSchema(
                name="edit_file",
                description="Edit a file by applying changes",
                arguments={"file": "str", "changes": "str"},
                required_fields=["file", "changes"],
            ),
            "run_command": ToolSchema(
                name="run_command",
                description="Execute a shell command",
                arguments={"command": "str"},
                required_fields=["command"],
            ),
            "update_memory": ToolSchema(
                name="update_memory",
                description="Update a memory block",
                arguments={"block_label": "str", "value": "str"},
                required_fields=["block_label", "value"],
            ),
        }
        return schemas

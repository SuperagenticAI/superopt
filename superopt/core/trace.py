"""
Execution Trace Definition

An execution trace τ captures all information about an agent's interaction
with its environment during a task execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FailureType(Enum):
    """Types of failures that can occur in agent execution."""

    PROMPT = "PROMPT"
    TOOL = "TOOL"
    RETRIEVAL = "RETRIEVAL"
    MEMORY = "MEMORY"
    NONE = "NONE"


@dataclass
class ToolCall:
    """Record of a tool invocation."""

    tool_name: str
    arguments: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: str | None = None
    return_value: Any | None = None


@dataclass
class RetrievalQuery:
    """Record of a retrieval query."""

    query: str
    retrieved_documents: list[dict[str, Any]] = field(default_factory=list)
    ranking_scores: list[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryAccess:
    """Record of memory read/write operations."""

    operation: str  # "read" or "write"
    entry_type: str | None = None
    content: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionTrace:
    """
    Complete execution trace capturing agent-environment interaction.

    This serves as the primary supervision signal for SuperOpt.
    """

    task_description: str
    task_id: str | None = None

    # Environment snapshot
    prompt_snapshot: dict[str, Any] | None = None

    # Execution records
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_errors: list[ToolCall] = field(default_factory=list)
    retrieval_queries: list[RetrievalQuery] = field(default_factory=list)
    memory_reads: list[MemoryAccess] = field(default_factory=list)
    memory_writes: list[MemoryAccess] = field(default_factory=list)
    model_outputs: list[str] = field(default_factory=list)

    # External execution results
    execution_results: dict[str, Any] | None = None
    compiler_errors: list[str] = field(default_factory=list)
    test_failures: list[str] = field(default_factory=list)
    runtime_exceptions: list[str] = field(default_factory=list)

    # Outcome
    success: bool = False
    failure_type: FailureType | None = None
    failure_message: str | None = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float | None = None
    token_count: int | None = None

    def has_tool_error(self) -> bool:
        """Check if trace contains tool errors."""
        return len(self.tool_errors) > 0

    def invalid_arguments(self) -> bool:
        """Check if trace contains invalid tool arguments."""
        return any(
            call.error_message and "invalid" in call.error_message.lower()
            for call in self.tool_errors
        )

    def missing_symbol(self) -> bool:
        """Check if trace indicates missing symbols (retrieval failure)."""
        if self.compiler_errors:
            error_text = " ".join(self.compiler_errors).lower()
            return any(
                keyword in error_text
                for keyword in ["undefined", "not found", "missing", "cannot find"]
            )
        return False

    def retrieval_empty(self) -> bool:
        """Check if retrieval queries returned empty results."""
        return any(len(query.retrieved_documents) == 0 for query in self.retrieval_queries)

    def violates_instruction(self) -> bool:
        """Check if trace shows instruction violations."""
        # This would need more sophisticated analysis
        # For now, check if output format errors exist
        return self.output_format_error()

    def output_format_error(self) -> bool:
        """Check if there are output format errors."""
        if self.execution_results:
            return self.execution_results.get("format_error", False)
        return False

    def repeats_known_mistake(self) -> bool:
        """Check if agent repeats a previously known mistake."""
        # This would require comparing against memory
        # For now, check if same error occurs multiple times
        if len(self.tool_errors) > 1:
            error_types = {call.error_message for call in self.tool_errors if call.error_message}
            return len(error_types) == 1  # Same error repeated
        return False

    def conflicts_with_memory(self) -> bool:
        """Check if trace conflicts with existing memory entries."""
        # This would require memory comparison logic
        return False

    def noisy_context(self) -> bool:
        """Check if retrieval returned noisy/irrelevant context."""
        if self.retrieval_queries:
            # Check if ranking scores are low
            for query in self.retrieval_queries:
                if query.ranking_scores:
                    avg_score = sum(query.ranking_scores) / len(query.ranking_scores)
                    if avg_score < 0.5:  # Threshold for noise
                        return True
        return False

    def summary(self) -> str:
        """Generate a human-readable summary of the trace."""
        parts = [f"Task: {self.task_description}"]

        if self.success:
            parts.append("Status: SUCCESS")
        else:
            parts.append(
                f"Status: FAILURE ({self.failure_type.value if self.failure_type else 'UNKNOWN'})"
            )
            if self.failure_message:
                parts.append(f"Error: {self.failure_message}")

        if self.tool_errors:
            parts.append(f"Tool Errors: {len(self.tool_errors)}")
            for error in self.tool_errors[:3]:  # Show first 3
                parts.append(f"  - {error.tool_name}: {error.error_message}")

        if self.compiler_errors:
            parts.append(f"Compiler Errors: {len(self.compiler_errors)}")
            for error in self.compiler_errors[:3]:
                parts.append(f"  - {error}")

        if self.retrieval_queries:
            parts.append(f"Retrieval Queries: {len(self.retrieval_queries)}")
            empty_queries = sum(
                1 for q in self.retrieval_queries if len(q.retrieved_documents) == 0
            )
            if empty_queries > 0:
                parts.append(f"  - Empty results: {empty_queries}")

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Serialize trace to dictionary."""
        return {
            "task_description": self.task_description,
            "task_id": self.task_id,
            "prompt_snapshot": self.prompt_snapshot,
            "tool_calls": [
                {
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "timestamp": call.timestamp.isoformat(),
                    "success": call.success,
                    "error_message": call.error_message,
                }
                for call in self.tool_calls
            ],
            "tool_errors": [
                {
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "error_message": call.error_message,
                }
                for call in self.tool_errors
            ],
            "retrieval_queries": [
                {
                    "query": q.query,
                    "retrieved_count": len(q.retrieved_documents),
                    "timestamp": q.timestamp.isoformat(),
                }
                for q in self.retrieval_queries
            ],
            "success": self.success,
            "failure_type": self.failure_type.value if self.failure_type else None,
            "failure_message": self.failure_message,
            "compiler_errors": self.compiler_errors,
            "test_failures": self.test_failures,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionTrace":
        """Deserialize trace from dictionary."""
        from datetime import datetime

        trace = cls(
            task_description=data["task_description"],
            task_id=data.get("task_id"),
            prompt_snapshot=data.get("prompt_snapshot"),
            success=data.get("success", False),
            failure_type=FailureType(data["failure_type"]) if data.get("failure_type") else None,
            failure_message=data.get("failure_message"),
            compiler_errors=data.get("compiler_errors", []),
            test_failures=data.get("test_failures", []),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            duration_seconds=data.get("duration_seconds"),
            token_count=data.get("token_count"),
        )

        # Reconstruct tool calls
        for call_data in data.get("tool_calls", []):
            trace.tool_calls.append(
                ToolCall(
                    tool_name=call_data["tool_name"],
                    arguments=call_data["arguments"],
                    timestamp=datetime.fromisoformat(
                        call_data.get("timestamp", datetime.now().isoformat())
                    ),
                    success=call_data.get("success", True),
                    error_message=call_data.get("error_message"),
                )
            )

        # Reconstruct tool errors
        for error_data in data.get("tool_errors", []):
            trace.tool_errors.append(
                ToolCall(
                    tool_name=error_data["tool_name"],
                    arguments=error_data["arguments"],
                    error_message=error_data.get("error_message"),
                    success=False,
                )
            )

        return trace

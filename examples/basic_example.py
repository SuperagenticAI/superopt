"""
Basic SuperOpt Example

Demonstrates how to use SuperOpt to optimize an agent environment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from superopt import AgenticEnvironment, ExecutionTrace, FailureType, SuperOpt
from superopt.core.environment import PromptConfig, RetrievalConfig, ToolSchema
from superopt.core.trace import ToolCall


def create_mock_trace(task_description: str, has_tool_error: bool = False) -> ExecutionTrace:
    """Create a mock execution trace for demonstration."""
    trace = ExecutionTrace(
        task_description=task_description,
        task_id=f"task_{datetime.now().timestamp()}",
        success=not has_tool_error,
    )

    if has_tool_error:
        # Simulate a tool error (0-indexed line number)
        trace.tool_errors.append(
            ToolCall(
                tool_name="edit_file",
                arguments={"file": "test.py", "line": 0},
                success=False,
                error_message="Line numbers must be 1-indexed, not 0-indexed",
            )
        )
        trace.failure_type = FailureType.TOOL

    return trace


def main():
    """Run a basic SuperOpt optimization example."""
    print("SuperOpt Basic Example")
    print("=" * 50)

    # Initialize environment
    environment = AgenticEnvironment(
        prompts=PromptConfig(
            system_prompt="You are a helpful coding assistant.",
        ),
        tools={
            "edit_file": ToolSchema(
                name="edit_file",
                description="Edit a file by applying changes",
                arguments={"file": "str", "line": "int"},
                required_fields=["file", "line"],
            ),
        },
        retrieval=RetrievalConfig(),
    )

    # Initialize SuperOpt
    optimizer = SuperOpt(
        environment=environment,
        alpha=1.0,
        use_stability_checks=True,
    )

    print("\n1. Initial Environment:")
    print(f"   Tool schema description: {environment.tools['edit_file'].description[:50]}...")

    # Simulate execution with tool error
    print("\n2. Executing task with tool error...")
    trace = create_mock_trace("Edit line 0 in test.py", has_tool_error=True)
    print(f"   Error: {trace.tool_errors[0].error_message}")

    # Optimize
    print("\n3. Optimizing environment...")
    optimizer.step(trace)

    # Check updated environment
    print("\n4. Updated Environment:")
    updated_desc = optimizer.environment.tools["edit_file"].description
    print(f"   Tool schema description length: {len(updated_desc)} chars")
    if len(updated_desc) > len(environment.tools["edit_file"].description):
        print("   ✓ Schema was updated with clarifications")

    # Check statistics
    stats = optimizer.get_statistics()
    print("\n5. Statistics:")
    print(f"   Controller diagnoses: {stats['controller_stats']}")
    print(f"   Optimization steps: {stats['optimization_steps']}")

    print("\n" + "=" * 50)
    print("Example completed!")


if __name__ == "__main__":
    main()

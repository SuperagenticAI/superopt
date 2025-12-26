#!/usr/bin/env python3
"""
Test script for enhanced Aider adapter.

Tests the Aider adapter with real execution to verify:
1. Adapter initialization
2. Environment extraction and application
3. Task execution with trace capture
4. Failure type classification

Usage:
    python scripts/test_aider_adapter.py [--subprocess] [--model MODEL]
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt.adapters.aider_adapter import AiderAdapter
from superopt.core.environment import AgenticEnvironment, PromptConfig, RetrievalConfig, ToolSchema


def create_test_environment() -> AgenticEnvironment:
    """Create a test environment with SuperOpt-style constraints."""
    return AgenticEnvironment(
        prompts=PromptConfig(
            system_prompt="""You are a helpful coding assistant.
Write clean, well-documented Python code.
Always use type hints where appropriate.""",
        ),
        tools={
            "edit_file": ToolSchema(
                name="edit_file",
                description="Edit a file. CRITICAL: line numbers are 1-indexed (>= 1).",
                arguments={
                    "file": "str - Path to file",
                    "line_number": "int - Line number (1-indexed, must be >= 1)",
                    "changes": "str - Changes to apply",
                },
                required_fields=["file", "changes"],
                constraints=[
                    "line_number must be >= 1 (1-indexed, not 0-indexed)",
                    "File paths must be relative to project root",
                ],
            ),
        },
        retrieval=RetrievalConfig(top_k=5, chunk_size=500),
    )


def test_aider_adapter(use_subprocess: bool = False, model: str = "ollama/llama3.1:8b"):
    """Test the Aider adapter with a simple task."""
    print("Testing Aider Adapter")
    print("=" * 60)
    print(f"Mode: {'subprocess' if use_subprocess else 'library (or subprocess fallback)'}")
    print(f"Model: {model}")
    print("=" * 60)

    # Create adapter
    print("\n1. Creating Aider adapter...")
    try:
        adapter = AiderAdapter(
            model_name=model,
            use_subprocess=use_subprocess,
        )
        info = adapter.get_agent_info()
        print("   [OK] Adapter created")
        print(f"     Mode: {info['mode']}")
        print(f"     Workspace: {info['workspace']}")
    except Exception as e:
        print(f"   [FAIL] Failed to create adapter: {e}")
        return False

    # Extract environment
    print("\n2. Extracting environment...")
    try:
        env = adapter.extract_environment()
        print("   [OK] Environment extracted")
        print(f"     Prompt: {env.prompts.system_prompt[:50]}...")
        print(f"     Tools: {list(env.tools.keys())}")
    except Exception as e:
        print(f"   [FAIL] Failed to extract environment: {e}")
        return False

    # Apply custom environment
    print("\n3. Applying custom environment...")
    try:
        custom_env = create_test_environment()
        adapter.apply_environment(custom_env)
        print("   [OK] Custom environment applied")
        print(f"     Constraints: {custom_env.tools['edit_file'].constraints}")
    except Exception as e:
        print(f"   [FAIL] Failed to apply environment: {e}")
        return False

    # Test execution
    print("\n4. Testing task execution...")
    test_task = "Create a Python file called hello.py with a function greet(name: str) -> str that returns 'Hello, {name}!'"

    try:
        print(f"   Task: {test_task[:60]}...")
        print("   Executing (this may take a moment)...")

        trace = adapter.execute(test_task, custom_env)

        print("\n   --- Trace Results ---")
        print(f"   Success: {trace.success}")
        print(f"   Failure Type: {trace.failure_type.value if trace.failure_type else 'None'}")
        print(f"   Duration: {trace.duration_seconds:.2f}s")
        print(f"   Tool Calls: {len(trace.tool_calls)}")
        print(f"   Tool Errors: {len(trace.tool_errors)}")
        print(f"   Compiler Errors: {len(trace.compiler_errors)}")
        print(f"   Runtime Exceptions: {len(trace.runtime_exceptions)}")

        if trace.failure_message:
            print(f"   Failure Message: {trace.failure_message[:100]}")

        if trace.model_outputs:
            preview = trace.model_outputs[0][:200] if trace.model_outputs[0] else ""
            print(f"   Output Preview: {preview}...")

        # Show tool calls
        if trace.tool_calls:
            print("\n   Tool Calls:")
            for tc in trace.tool_calls[:3]:
                print(f"     - {tc.tool_name}: {tc.success}")

        # Show errors
        if trace.tool_errors:
            print("\n   Tool Errors:")
            for te in trace.tool_errors[:3]:
                err_msg = te.error_message[:80] if te.error_message else "No message"
                print(f"     - {err_msg}")

        success = True

    except Exception as e:
        print(f"   [FAIL] Execution failed: {e}")
        import traceback

        traceback.print_exc()
        success = False

    # Show trace buffer summary
    print("\n5. Trace buffer summary...")
    traces = adapter.get_trace_buffer()
    print(f"   Total traces: {len(traces)}")
    for i, t in enumerate(traces):
        status = "SUCCESS" if t.success else f"FAIL:{t.failure_type.value}"
        print(f"   [{i + 1}] {t.task_description[:40]}... -> {status}")

    # Cleanup
    print("\n6. Cleaning up...")
    adapter.cleanup()
    print("   [OK] Cleanup complete")

    print("\n" + "=" * 60)
    if success:
        print("TEST COMPLETED - Adapter is working!")
    else:
        print("TEST COMPLETED - Some issues detected (see above)")
    print("=" * 60)

    return success


def main():
    parser = argparse.ArgumentParser(description="Test Aider adapter")
    parser.add_argument(
        "--subprocess",
        action="store_true",
        help="Force subprocess mode (CLI invocation)",
    )
    parser.add_argument(
        "--model",
        default="ollama/llama3.1:8b",
        help="Model to use (default: ollama/llama3.1:8b)",
    )
    args = parser.parse_args()

    success = test_aider_adapter(
        use_subprocess=args.subprocess,
        model=args.model,
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

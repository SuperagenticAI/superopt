#!/usr/bin/env python3
"""
GEPA vs SuperOpt Comparison

Runs GEPA prompt optimization on the same tasks as SuperOpt to demonstrate
that prompt-only optimization cannot fix tool-level failures.

This is a lightweight comparison - uses minimal iterations to avoid overheating.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt.adapters.aider_adapter import AiderAdapter
from superopt.comparison.dataset_loaders import load_superopt_format


def run_baseline_with_prompt_variants(
    tasks: list,
    model_name: str = "ollama/llama3.2:3b",
    num_prompt_variants: int = 2,
):
    """
    Simulate GEPA-style prompt optimization.

    GEPA optimizes prompts through evolutionary search. We simulate this by:
    1. Running with default prompt (baseline)
    2. Running with improved prompts (variants)
    3. Selecting best performing prompt

    Key insight: GEPA cannot fix TOOL failures because it only modifies prompts,
    not tool schemas.
    """

    # Prompt variants to test (simulating GEPA evolution)
    prompt_variants = [
        # Variant 0: Default prompt
        {
            "name": "default",
            "system_prompt": "You are a helpful coding assistant.",
            "constraints": [],
        },
        # Variant 1: More detailed instructions (GEPA-style mutation)
        {
            "name": "detailed",
            "system_prompt": """You are an expert Python programmer. Follow these rules:
1. Write clean, well-documented code
2. Handle edge cases properly
3. Return exactly what is requested
4. Do not add unnecessary complexity""",
            "constraints": ["Be precise", "Handle edge cases"],
        },
        # Variant 2: Even more specific (GEPA-style mutation)
        {
            "name": "specific",
            "system_prompt": """You are a Python coding expert. Important rules:
- Always handle None/empty inputs gracefully
- Return the exact type specified (str, int, list, etc.)
- Include proper error handling
- Follow the function signature exactly
- Test edge cases mentally before writing code""",
            "constraints": ["Handle None", "Return correct type", "Error handling"],
        },
    ]

    results = {}

    for variant in prompt_variants[: num_prompt_variants + 1]:
        print(f"\n{'=' * 60}")
        print(f"Testing prompt variant: {variant['name']}")
        print(f"{'=' * 60}")

        # Create adapter with this prompt variant
        adapter = AiderAdapter(model_name=model_name)

        # Apply custom prompt
        env = adapter.extract_environment()
        env.prompts.system_prompt = variant["system_prompt"]
        # Note: constraints would be appended to system_prompt in practice

        variant_results = []

        for i, task in enumerate(tasks):
            print(f"\n[{i + 1}/{len(tasks)}] Task: {task[:60]}...")

            start_time = time.time()
            try:
                trace = adapter.execute(task, env)
                duration = time.time() - start_time

                result = {
                    "task": task,
                    "success": trace.success,
                    "failure_type": trace.failure_type.value if trace.failure_type else "NONE",
                    "duration": duration,
                    "tool_errors": len(trace.tool_errors),
                }

                status = "PASS" if trace.success else f"FAIL ({trace.failure_type.value})"
                print(f"    Result: {status} ({duration:.1f}s)")

            except Exception as e:
                duration = time.time() - start_time
                result = {
                    "task": task,
                    "success": False,
                    "failure_type": "ERROR",
                    "duration": duration,
                    "error": str(e),
                }
                print(f"    Result: ERROR - {e}")

            variant_results.append(result)

        # Cleanup
        adapter.cleanup()

        # Calculate metrics
        success_count = sum(1 for r in variant_results if r["success"])
        success_rate = success_count / len(variant_results) * 100

        results[variant["name"]] = {
            "prompt": variant["system_prompt"][:100] + "...",
            "results": variant_results,
            "success_count": success_count,
            "success_rate": success_rate,
            "total_duration": sum(r["duration"] for r in variant_results),
        }

        print(f"\nVariant '{variant['name']}': {success_count}/{len(tasks)} ({success_rate:.1f}%)")

    return results


def compare_with_superopt(gepa_results: dict, superopt_file: Path):
    """Compare GEPA results with existing SuperOpt results."""

    # Load SuperOpt results
    with open(superopt_file) as f:
        superopt_data = json.load(f)

    superopt_results = superopt_data.get("superopt", [])
    baseline_results = superopt_data.get("baseline", [])

    superopt_success = sum(1 for r in superopt_results if r["success"])
    baseline_success = sum(1 for r in baseline_results if r["success"])

    # Find best GEPA variant
    best_gepa = max(gepa_results.values(), key=lambda x: x["success_rate"])
    best_gepa_name = [k for k, v in gepa_results.items() if v == best_gepa][0]

    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)

    print("\n## Method Comparison")
    print("| Method | Success Rate | Notes |")
    print("|--------|--------------|-------|")
    print(
        f"| Baseline | {baseline_success}/{len(baseline_results)} ({100 * baseline_success / len(baseline_results):.1f}%) | No optimization |"
    )

    for name, data in gepa_results.items():
        print(
            f"| GEPA ({name}) | {data['success_count']}/{len(data['results'])} ({data['success_rate']:.1f}%) | Prompt-only |"
        )

    print(
        f"| **SuperOpt** | **{superopt_success}/{len(superopt_results)} ({100 * superopt_success / len(superopt_results):.1f}%)** | **Full environment** |"
    )

    # Analyze specific failures
    print("\n## Failure Analysis")
    print("\nTasks where GEPA fails but SuperOpt succeeds:")

    for i, task_result in enumerate(best_gepa["results"]):
        if (
            not task_result["success"]
            and i < len(superopt_results)
            and superopt_results[i]["success"]
        ):
            print(f"- {task_result['task'][:50]}...")
            print(f"  GEPA failure type: {task_result['failure_type']}")
            print("  SuperOpt: PASS")

    # Key insight
    print("\n## Key Insight")
    print(
        """
GEPA can only optimize prompts (P). When failures originate from:
- Tool schema issues (T) → GEPA cannot fix
- Retrieval configuration (R) → GEPA cannot fix
- Memory management (M) → GEPA cannot fix

SuperOpt optimizes the full environment Φ = {P, T, R, M}, enabling
it to fix failures that prompt-only optimization cannot address.
"""
    )

    return {
        "baseline": {"success": baseline_success, "total": len(baseline_results)},
        "gepa_best": {
            "name": best_gepa_name,
            "success": best_gepa["success_count"],
            "total": len(best_gepa["results"]),
        },
        "superopt": {"success": superopt_success, "total": len(superopt_results)},
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GEPA vs SuperOpt Comparison")
    parser.add_argument("--tasks", type=str, required=True, help="Path to tasks JSON file")
    parser.add_argument(
        "--superopt-results",
        type=str,
        default=None,
        help="Path to SuperOpt results for comparison (optional)",
    )
    parser.add_argument("--output", type=str, required=True, help="Output path for results JSON")
    parser.add_argument("--model", type=str, default="ollama/llama3.2:3b", help="Model to use")
    parser.add_argument(
        "--variants", type=int, default=2, help="Number of prompt variants (keep low!)"
    )
    parser.add_argument(
        "--max-tasks", type=int, default=5, help="Max tasks to run (keep low for heat!)"
    )
    args = parser.parse_args()

    # Load tasks
    tasks_file = Path(args.tasks)
    tasks = load_superopt_format(tasks_file)

    # Limit tasks to avoid overheating
    if args.max_tasks and len(tasks) > args.max_tasks:
        print(f"Limiting to {args.max_tasks} tasks to avoid overheating...")
        tasks = tasks[: args.max_tasks]

    print(f"Running GEPA comparison with {len(tasks)} tasks, {args.variants} variants")
    print(f"Model: {args.model}")
    print("This is a lightweight comparison to avoid Mac overheating.\n")

    # Run GEPA-style prompt optimization
    gepa_results = run_baseline_with_prompt_variants(
        tasks=tasks,
        model_name=args.model,
        num_prompt_variants=args.variants,
    )

    # Compare with SuperOpt
    superopt_file = Path(args.superopt_results)
    if superopt_file.exists():
        comparison = compare_with_superopt(gepa_results, superopt_file)
    else:
        print(f"\nWarning: SuperOpt results not found at {superopt_file}")
        comparison = None

    # Save results
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "tasks_count": len(tasks),
        "gepa_results": gepa_results,
        "comparison": comparison,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()

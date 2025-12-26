#!/usr/bin/env python3
"""
Evaluate SuperOpt Full Optimization

Runs tasks with SuperOpt's full environment optimization and compares against baseline.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt import SuperOpt
from superopt.comparison import ComparisonFramework
from superopt.comparison.dataset_loaders import load_superopt_format
from superopt.comparison.models import create_llm_client, get_model_config


def main():
    parser = argparse.ArgumentParser(description="Evaluate SuperOpt full optimization")
    parser.add_argument("--tasks", type=str, required=True, help="Path to tasks file (JSON)")
    parser.add_argument("--output", type=str, required=True, help="Output file for results")
    parser.add_argument(
        "--agent",
        type=str,
        default="aider",
        choices=["aider", "letta", "codex"],
        help="Agent adapter to use",
    )
    parser.add_argument(
        "--model-config",
        type=str,
        default="local_large",
        help="Model configuration name (default: local_large for gpt-oss:20b + 120b)",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=None,
        help="API base URL (for Ollama, e.g., http://localhost:11434)",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=10, help="Maximum optimization iterations per task"
    )
    parser.add_argument(
        "--alpha", type=float, default=1.0, help="Update acceptance rate (0.0 to 1.0)"
    )
    args = parser.parse_args()

    # Load tasks
    tasks_file = Path(args.tasks)
    task_descriptions = load_superopt_format(tasks_file)

    if not task_descriptions:
        print(f"Error: No tasks found in {tasks_file}")
        return

    print(f"Loaded {len(task_descriptions)} tasks")

    # Get model config first (needed for agent adapter)
    model_config = get_model_config(args.model_config)

    # Update api_base if provided
    if args.api_base and model_config.provider.value == "ollama":
        from dataclasses import replace

        model_config = replace(model_config, api_base=args.api_base)

    # Get model name for agent (use task_model from config)
    agent_model = model_config.task_model

    # Setup agent adapter
    if args.agent == "aider":
        from superopt.adapters.aider_adapter import AiderAdapter

        agent_adapter = AiderAdapter(model_name=agent_model)
    elif args.agent == "letta":
        from superopt.adapters.letta_adapter import LettaAdapter

        agent_adapter = LettaAdapter()
    elif args.agent == "codex":
        from superopt.adapters.codex_adapter import CodexAdapter

        agent_adapter = CodexAdapter()
    else:
        raise ValueError(f"Unknown agent: {args.agent}")

    # Create LLM client for SuperOpt
    llm_client = create_llm_client(model_config)

    # Get initial environment from agent
    initial_env = agent_adapter.extract_environment()

    # Create SuperOpt optimizer
    superopt_optimizer = SuperOpt(
        environment=initial_env,
        llm_client=llm_client,
        alpha=args.alpha,
        use_stability_checks=True,
    )

    # Create framework
    framework = ComparisonFramework(
        tasks=task_descriptions,
        agent_adapter=agent_adapter,
        superopt_optimizer=superopt_optimizer,
        model_config=model_config,
    )

    # Run baseline first for comparison
    print("Running baseline evaluation...")
    baseline_results = framework.run_baseline()

    # Run SuperOpt optimization
    print(f"Running SuperOpt optimization (max_iterations={args.max_iterations})...")
    superopt_results = framework.run_superopt()

    # Combine results
    results = {
        "baseline": baseline_results,
        "superopt": superopt_results,
    }

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    baseline_success = sum(1 for r in baseline_results if r["success"])
    superopt_success = sum(1 for r in superopt_results if r["success"])

    # Calculate average iterations
    avg_iterations = (
        sum(r.get("optimization_steps", 0) for r in superopt_results) / len(superopt_results)
        if superopt_results
        else 0
    )

    print("\nSuperOpt evaluation complete!")
    print(f"  Tasks: {len(task_descriptions)}")
    print(
        f"  Baseline success: {baseline_success}/{len(baseline_results)} ({100 * baseline_success / len(baseline_results):.1f}%)"
    )
    print(
        f"  SuperOpt success: {superopt_success}/{len(superopt_results)} ({100 * superopt_success / len(superopt_results):.1f}%)"
    )
    print(
        f"  Improvement: {superopt_success - baseline_success} tasks ({100 * (superopt_success - baseline_success) / len(superopt_results):.1f}%)"
    )
    print(f"  Average optimization steps: {avg_iterations:.1f}")
    print(f"  Results saved to: {output_path}")


if __name__ == "__main__":
    main()

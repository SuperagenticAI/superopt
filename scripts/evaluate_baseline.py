#!/usr/bin/env python3
"""
Evaluate Baseline (No Optimization)

Runs tasks with static agent configuration (no optimization).
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt.comparison import ComparisonFramework
from superopt.comparison.dataset_loaders import load_superopt_format
from superopt.comparison.models import get_model_config


def main():
    parser = argparse.ArgumentParser(description="Evaluate baseline (no optimization)")
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
    args = parser.parse_args()

    # Load tasks
    tasks_file = Path(args.tasks)
    task_descriptions = load_superopt_format(tasks_file)

    if not task_descriptions:
        print(f"Error: No tasks found in {tasks_file}")
        return

    print(f"Loaded {len(task_descriptions)} tasks")

    # Setup agent adapter
    if args.agent == "aider":
        from superopt.adapters.aider_adapter import AiderAdapter

        agent_adapter = AiderAdapter()
    elif args.agent == "letta":
        from superopt.adapters.letta_adapter import LettaAdapter

        agent_adapter = LettaAdapter()
    elif args.agent == "codex":
        from superopt.adapters.codex_adapter import CodexAdapter

        agent_adapter = CodexAdapter()
    else:
        raise ValueError(f"Unknown agent: {args.agent}")

    # Get model config
    model_config = get_model_config(args.model_config)

    # Update api_base if provided
    if args.api_base and model_config.provider.value == "ollama":
        from dataclasses import replace

        model_config = replace(model_config, api_base=args.api_base)

    # Create framework (no optimizer, no adapters - just baseline)
    framework = ComparisonFramework(
        tasks=task_descriptions,
        agent_adapter=agent_adapter,
        superopt_optimizer=None,
        model_config=model_config,
    )

    # Run baseline
    print("Running baseline evaluation...")
    results = framework.run_baseline()

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    success_count = sum(1 for r in results if r["success"])
    print("\nBaseline evaluation complete!")
    print(f"  Tasks: {len(results)}")
    print(f"  Success: {success_count}/{len(results)} ({100 * success_count / len(results):.1f}%)")
    print(f"  Results saved to: {output_path}")


if __name__ == "__main__":
    main()

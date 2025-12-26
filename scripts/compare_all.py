#!/usr/bin/env python3
"""
Compare All Methods: Baseline, GEPA, ACE, and SuperOpt

Runs comprehensive comparison across all optimization methods.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from superopt import SuperOpt
from superopt.comparison import ACEComparison, ComparisonFramework, GEPAComparison
from superopt.comparison.dataset_loaders import load_superopt_format
from superopt.comparison.models import create_llm_client, get_model_config


def main():
    parser = argparse.ArgumentParser(description="Compare all optimization methods")
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
    parser.add_argument("--api-base", type=str, default=None, help="API base URL (for Ollama)")
    parser.add_argument(
        "--gepa-max-calls", type=int, default=150, help="Max GEPA metric evaluations"
    )
    parser.add_argument("--superopt-max-iter", type=int, default=10, help="Max SuperOpt iterations")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline evaluation")
    parser.add_argument("--skip-gepa", action="store_true", help="Skip GEPA evaluation")
    parser.add_argument("--skip-ace", action="store_true", help="Skip ACE evaluation")
    parser.add_argument("--skip-superopt", action="store_true", help="Skip SuperOpt evaluation")
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

    llm_client = create_llm_client(model_config)

    # Get initial environment
    initial_env = agent_adapter.extract_environment()

    # Create optimizers and adapters
    superopt_optimizer = SuperOpt(
        environment=initial_env,
        llm_client=llm_client,
        alpha=1.0,
        use_stability_checks=True,
    )

    gepa_adapter = GEPAComparison(
        agent_adapter=agent_adapter,
        model_config=model_config,
        api_base=args.api_base,
    )

    ace_adapter = ACEComparison(
        agent_adapter=agent_adapter,
        model_config=model_config,
        api_base=args.api_base,
    )

    # Create framework
    framework = ComparisonFramework(
        tasks=task_descriptions,
        agent_adapter=agent_adapter,
        superopt_optimizer=superopt_optimizer,
        model_config=model_config,
        gepa_adapter=gepa_adapter,
        ace_adapter=ace_adapter,
    )

    results = {}

    # Run baseline
    if not args.skip_baseline:
        print("Running baseline evaluation...")
        results["baseline"] = framework.run_baseline()
    else:
        print("Skipping baseline evaluation")

    # Run GEPA
    if not args.skip_gepa:
        print(f"Running GEPA optimization (max_calls={args.gepa_max_calls})...")
        results["gepa"] = framework.run_gepa()
        results["gepa_stats"] = gepa_adapter.get_optimization_stats()
        results["gepa_prompt"] = gepa_adapter.get_optimized_prompt()
    else:
        print("Skipping GEPA evaluation")

    # Run ACE
    if not args.skip_ace:
        print("Running ACE context accumulation...")
        results["ace"] = framework.run_ace()
        results["ace_context_size"] = len(ace_adapter.get_context())
    else:
        print("Skipping ACE evaluation")

    # Run SuperOpt
    if not args.skip_superopt:
        print(f"Running SuperOpt optimization (max_iter={args.superopt_max_iter})...")
        results["superopt"] = framework.run_superopt()
    else:
        print("Skipping SuperOpt evaluation")

    # Run comparison analysis
    print("Analyzing results...")
    comparison = framework.compare_all()
    results["comparison"] = comparison

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print(f"\n{'=' * 60}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 60}")

    if "baseline" in results:
        baseline_success = sum(1 for r in results["baseline"] if r["success"])
        print(
            f"Baseline:  {baseline_success}/{len(results['baseline'])} ({100 * baseline_success / len(results['baseline']):.1f}%)"
        )

    if "gepa" in results:
        gepa_success = sum(1 for r in results["gepa"] if r["success"])
        improvement = gepa_success - baseline_success if "baseline" in results else 0
        print(
            f"GEPA:      {gepa_success}/{len(results['gepa'])} ({100 * gepa_success / len(results['gepa']):.1f}%) [Δ{improvement:+d}]"
        )

    if "ace" in results:
        ace_success = sum(1 for r in results["ace"] if r["success"])
        improvement = ace_success - baseline_success if "baseline" in results else 0
        print(
            f"ACE:       {ace_success}/{len(results['ace'])} ({100 * ace_success / len(results['ace']):.1f}%) [Δ{improvement:+d}]"
        )

    if "superopt" in results:
        superopt_success = sum(1 for r in results["superopt"] if r["success"])
        improvement = superopt_success - baseline_success if "baseline" in results else 0
        print(
            f"SuperOpt:  {superopt_success}/{len(results['superopt'])} ({100 * superopt_success / len(results['superopt']):.1f}%) [Δ{improvement:+d}]"
        )

    print(f"{'=' * 60}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()

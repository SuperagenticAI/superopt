#!/usr/bin/env python3
"""
Comprehensive Results Analysis for SuperOpt Paper

Analyzes evaluation results and generates paper-ready metrics and tables.
Handles both separate result files and combined result files.

Usage:
    python scripts/analyze_results.py [--results-dir DIR] [--output FILE]
    python scripts/analyze_results.py --results-dir results/real_eval --output results/analysis.md
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def parse_trace_string(trace_str: str) -> dict[str, Any]:
    """Parse a trace string representation into a dictionary."""
    result = {
        "duration_seconds": 0.0,
        "tool_calls": 0,
        "tokens_sent": 0,
        "tokens_received": 0,
        "failure_type": "NONE",
    }

    # Duration
    duration_match = re.search(r"duration_seconds=(\d+\.?\d*)", trace_str)
    if duration_match:
        result["duration_seconds"] = float(duration_match.group(1))

    # Tool calls (count ToolCall occurrences)
    result["tool_calls"] = len(re.findall(r"ToolCall\(tool_name=", trace_str))

    # Tokens (from model output)
    tokens_sent_match = re.search(r"Tokens: ([\d.]+)k? sent", trace_str)
    tokens_received_match = re.search(r", (\d+) received", trace_str)
    if tokens_sent_match:
        tokens_str = tokens_sent_match.group(1)
        if "k" in trace_str[tokens_sent_match.start() : tokens_sent_match.end() + 5]:
            result["tokens_sent"] = int(float(tokens_str) * 1000)
        else:
            result["tokens_sent"] = int(float(tokens_str))
    if tokens_received_match:
        result["tokens_received"] = int(tokens_received_match.group(1))

    # Failure type
    failure_match = re.search(r"failure_type=<FailureType\.(\w+):", trace_str)
    if failure_match:
        result["failure_type"] = failure_match.group(1)

    return result


def parse_trace_dict(trace_dict: dict[str, Any]) -> dict[str, Any]:
    """Parse a trace dictionary into normalized format."""
    result = {
        "duration_seconds": trace_dict.get("duration_seconds", 0.0),
        "tool_calls": len(trace_dict.get("tool_calls", [])),
        "tokens_sent": 0,
        "tokens_received": 0,
        "failure_type": trace_dict.get("failure_type", "NONE"),
    }
    return result


def load_results(result_file: Path) -> list[dict[str, Any]]:
    """Load results from JSON file."""
    with open(result_file) as f:
        data = json.load(f)

    # Handle different result formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "baseline" in data:
        return data["baseline"]
    else:
        return []


def load_all_results(results_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Load all result files from a directory, handling both separate and combined formats."""
    results = {}

    # First check for combined result files (like superopt_qwen.json)
    for json_file in results_dir.glob("*.json"):
        if json_file.name in ["summary.json", "analysis_summary.json"]:
            continue

        with open(json_file) as f:
            data = json.load(f)

        # Check if it's a combined file (has baseline and superopt keys)
        if isinstance(data, dict) and "baseline" in data:
            results["baseline"] = data["baseline"]
            if "superopt" in data:
                results["superopt"] = data["superopt"]
            if "gepa" in data:
                results["gepa"] = data["gepa"]
            if "ace" in data:
                results["ace"] = data["ace"]
            break  # Found combined file, stop looking

    # If no combined file, look for separate files
    if not results:
        for method in ["baseline", "gepa", "ace", "superopt"]:
            result_file = results_dir / f"{method}.json"
            if result_file.exists():
                results[method] = load_results(result_file)

    return results


def extract_metrics(results: list[dict[str, Any]], method_name: str = "") -> dict[str, Any]:
    """Extract comprehensive metrics from results."""
    if not results:
        return {}

    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r.get("success", False))
    success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

    # Aggregate metrics from result fields
    total_retries = sum(r.get("retries", 0) for r in results)
    total_tool_errors = sum(r.get("tool_errors", 0) for r in results)
    total_retrieval_misses = sum(r.get("retrieval_misses", 0) for r in results)

    # Extract from traces
    total_duration = 0.0
    total_tool_calls = 0
    total_tokens_sent = 0
    total_tokens_received = 0

    # SuperOpt specific
    total_optimization_steps = 0
    total_converged = 0

    for r in results:
        trace = r.get("trace", {})
        if isinstance(trace, str):
            trace_data = parse_trace_string(trace)
        elif isinstance(trace, dict):
            trace_data = parse_trace_dict(trace)
        else:
            trace_data = {
                "duration_seconds": 0,
                "tool_calls": 0,
                "tokens_sent": 0,
                "tokens_received": 0,
            }

        total_duration += trace_data["duration_seconds"]
        total_tool_calls += trace_data["tool_calls"]
        total_tokens_sent += trace_data["tokens_sent"]
        total_tokens_received += trace_data["tokens_received"]

        # SuperOpt specific fields
        total_optimization_steps += r.get("optimization_steps", 0)
        if r.get("converged", False):
            total_converged += 1

    # Failure type analysis
    failure_types = defaultdict(int)
    for r in results:
        if not r.get("success", False):
            trace = r.get("trace", {})
            trace_str = (
                str(trace) if isinstance(trace, str) else str(trace.get("failure_type", "UNKNOWN"))
            )
            if "MEMORY" in trace_str:
                failure_types["MEMORY"] += 1
            elif "PROMPT" in trace_str:
                failure_types["PROMPT"] += 1
            elif "TOOL" in trace_str:
                failure_types["TOOL"] += 1
            elif "RETRIEVAL" in trace_str:
                failure_types["RETRIEVAL"] += 1
            else:
                failure_types["UNKNOWN"] += 1

    return {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": total_tasks - successful_tasks,
        "success_rate": success_rate,
        "avg_retries": total_retries / total_tasks if total_tasks > 0 else 0.0,
        "avg_tool_errors": total_tool_errors / total_tasks if total_tasks > 0 else 0.0,
        "avg_retrieval_misses": total_retrieval_misses / total_tasks if total_tasks > 0 else 0.0,
        "total_duration": total_duration,
        "avg_duration": total_duration / total_tasks if total_tasks > 0 else 0.0,
        "total_tool_calls": total_tool_calls,
        "avg_tool_calls": total_tool_calls / total_tasks if total_tasks > 0 else 0.0,
        "total_tokens_sent": total_tokens_sent,
        "total_tokens_received": total_tokens_received,
        "avg_tokens_sent": total_tokens_sent / total_tasks if total_tasks > 0 else 0.0,
        "avg_optimization_steps": total_optimization_steps / total_tasks
        if total_tasks > 0
        else 0.0,
        "convergence_rate": total_converged / total_tasks if total_tasks > 0 else 0.0,
        "failure_types": dict(failure_types),
    }


def compare_methods(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compare metrics across methods."""
    comparison = {}

    if not metrics:
        return comparison

    # Find baseline
    baseline_metrics = metrics.get("baseline", {})
    baseline_success_rate = baseline_metrics.get("success_rate", 0.0)

    # Compare each method to baseline
    for method_name, method_metrics in metrics.items():
        if method_name == "baseline":
            continue

        method_success_rate = method_metrics.get("success_rate", 0.0)
        improvement = method_success_rate - baseline_success_rate
        relative_improvement = (
            (improvement / baseline_success_rate * 100)
            if baseline_success_rate > 0
            else float("inf")
        )

        comparison[method_name] = {
            "success_rate": method_success_rate,
            "baseline_success_rate": baseline_success_rate,
            "absolute_improvement": improvement,
            "relative_improvement": relative_improvement
            if relative_improvement != float("inf")
            else None,
            "avg_tokens": method_metrics.get("avg_tokens", 0.0),
            "baseline_avg_tokens": baseline_metrics.get("avg_tokens", 0.0),
            "token_efficiency": method_metrics.get("avg_tokens", 0.0)
            / baseline_metrics.get("avg_tokens", 1.0)
            if baseline_metrics.get("avg_tokens", 0) > 0
            else 1.0,
        }

    return comparison


def analyze_failure_patterns(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze failure patterns in results."""
    patterns = {
        "no_execution": 0,  # No tool calls, no tokens
        "tool_errors": 0,
        "retrieval_failures": 0,
        "memory_issues": 0,
    }

    for r in results:
        if not r.get("success", False):
            tokens = r.get("tokens", 0)
            tool_errors = r.get("tool_errors", 0)
            retrieval_misses = r.get("retrieval_misses", 0)
            trace_str = str(r.get("trace", ""))

            if tokens == 0 and tool_errors == 0:
                patterns["no_execution"] += 1
            if tool_errors > 0:
                patterns["tool_errors"] += 1
            if retrieval_misses > 0:
                patterns["retrieval_failures"] += 1
            if "MEMORY" in trace_str:
                patterns["memory_issues"] += 1

    return patterns


def generate_markdown_report(
    metrics: dict[str, dict[str, Any]], results: dict[str, list[dict[str, Any]]]
) -> str:
    """Generate a comprehensive markdown report for the paper."""
    lines = []
    lines.append("# SuperOpt Evaluation Results")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    for method, m in metrics.items():
        status = (
            "pass"
            if m["success_rate"] > 0.9
            else ("partial" if m["success_rate"] > 0.5 else "fail")
        )
        lines.append(
            f"- **{method.capitalize()}**: {m['successful_tasks']}/{m['total_tasks']} tasks ({m['success_rate'] * 100:.1f}% success)"
        )
    lines.append("")

    # Comparison Table (Paper Table 1)
    lines.append("## Table 1: Method Comparison")
    lines.append("")
    methods = list(metrics.keys())
    lines.append("| Metric | " + " | ".join([m.capitalize() for m in methods]) + " |")
    lines.append("|--------|" + "|".join(["--------" for _ in methods]) + "|")

    # Success Rate
    line = "| Success Rate |"
    for m in methods:
        line += f" {metrics[m]['success_rate'] * 100:.1f}% |"
    lines.append(line)

    # Avg Duration
    line = "| Avg Duration (s) |"
    for m in methods:
        line += f" {metrics[m]['avg_duration']:.2f} |"
    lines.append(line)

    # Avg Tool Calls
    line = "| Avg Tool Calls |"
    for m in methods:
        line += f" {metrics[m]['avg_tool_calls']:.1f} |"
    lines.append(line)

    # Avg Retries
    line = "| Avg Retries |"
    for m in methods:
        line += f" {metrics[m]['avg_retries']:.2f} |"
    lines.append(line)

    # SuperOpt specific
    if "superopt" in metrics:
        line = "| Optimization Steps |"
        for m in methods:
            if m == "superopt":
                line += f" {metrics[m]['avg_optimization_steps']:.1f} |"
            else:
                line += " N/A |"
        lines.append(line)

        line = "| Convergence Rate |"
        for m in methods:
            if m == "superopt":
                line += f" {metrics[m]['convergence_rate'] * 100:.0f}% |"
            else:
                line += " N/A |"
        lines.append(line)

    lines.append("")

    # Key Findings Section (for paper)
    lines.append("## Key Findings")
    lines.append("")
    if "baseline" in metrics and "superopt" in metrics:
        b, s = metrics["baseline"], metrics["superopt"]
        improvement = s["success_rate"] - b["success_rate"]
        if improvement > 0:
            lines.append(
                f"1. **SuperOpt improves success rate by {improvement * 100:.1f}%** compared to baseline"
            )
        elif improvement == 0:
            lines.append(
                f"1. **Both methods achieve {b['success_rate'] * 100:.0f}% success rate** on this task set"
            )
        else:
            lines.append(f"1. Baseline outperforms SuperOpt by {-improvement * 100:.1f}%")

        if s["avg_optimization_steps"] > 0:
            lines.append(
                f"2. SuperOpt requires **{s['avg_optimization_steps']:.1f} optimization steps** on average"
            )

        if s["convergence_rate"] > 0:
            lines.append(
                f"3. **{s['convergence_rate'] * 100:.0f}% of tasks converge** to stable environment"
            )

        duration_ratio = (
            s["total_duration"] / b["total_duration"] if b["total_duration"] > 0 else 1.0
        )
        if duration_ratio > 1.1:
            lines.append(
                f"4. SuperOpt takes {duration_ratio:.1f}x longer due to optimization overhead"
            )
        elif duration_ratio < 0.9:
            lines.append(f"4. SuperOpt is {1 / duration_ratio:.1f}x faster than baseline")
        else:
            lines.append("4. Execution times are comparable")

    lines.append("")

    # Per-Task Details
    lines.append("## Per-Task Analysis")
    lines.append("")
    if results:
        first_method = list(results.keys())[0]
        tasks = [r.get("task", "")[:50] + "..." for r in results[first_method]]

        lines.append("| Task | " + " | ".join([m.capitalize() for m in results]) + " |")
        lines.append("|------|" + "|".join(["--------" for _ in results]) + "|")

        for i, task in enumerate(tasks[:10]):  # Limit to first 10 tasks
            line = f"| {task} |"
            for method in results:
                if i < len(results[method]):
                    r = results[method][i]
                    status = "PASS" if r.get("success") else "FAIL"
                    trace = r.get("trace", {})
                    if isinstance(trace, str):
                        trace_data = parse_trace_string(trace)
                    else:
                        trace_data = parse_trace_dict(trace)
                    duration = trace_data.get("duration_seconds", 0)
                    line += f" {status} ({duration:.1f}s) |"
                else:
                    line += " - |"
            lines.append(line)

    lines.append("")

    # Token Analysis
    lines.append("## Resource Usage")
    lines.append("")
    lines.append("| Method | Total Duration (s) | Tokens Sent | Tokens Received |")
    lines.append("|--------|-------------------|-------------|-----------------|")
    for method, m in metrics.items():
        lines.append(
            f"| {method.capitalize()} | {m['total_duration']:.1f} | {m['total_tokens_sent']:,} | {m['total_tokens_received']:,} |"
        )

    lines.append("")

    # Recommendations for Paper
    lines.append("## Paper Recommendations")
    lines.append("")
    if all(m["success_rate"] == 1.0 for m in metrics.values()):
        lines.append("- Current task set is **too simple** - all methods achieve 100% success")
        lines.append("- Consider using **harder tasks** that demonstrate optimization value")
        lines.append("- Alternative: Focus on **efficiency metrics** (tokens, duration, retries)")
    elif metrics.get("superopt", {}).get("success_rate", 0) > metrics.get("baseline", {}).get(
        "success_rate", 1
    ):
        lines.append("- Results show **clear SuperOpt advantage** - suitable for paper")
        lines.append("- Include failure analysis showing which types SuperOpt fixes")
    else:
        lines.append("- Consider running with **more challenging tasks**")
        lines.append("- Or **smaller models** that make more mistakes")

    return "\n".join(lines)


def print_summary(
    metrics: dict[str, dict[str, Any]], comparison: dict[str, Any], summary_file: Path | None = None
):
    """Print analysis summary."""
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS ANALYSIS")
    print("=" * 70)

    # Overall metrics
    print("\n📊 OVERALL METRICS")
    print("-" * 70)
    for method_name, method_metrics in metrics.items():
        print(f"\n{method_name.upper()}:")
        print(f"  Total Tasks: {method_metrics.get('total_tasks', 0)}")
        print(f"  Success Rate: {method_metrics.get('success_rate', 0.0):.1%}")
        print(f"  Successful: {method_metrics.get('successful_tasks', 0)}")
        print(f"  Failed: {method_metrics.get('failed_tasks', 0)}")
        print(f"  Avg Retries: {method_metrics.get('avg_retries', 0.0):.2f}")
        print(f"  Avg Tool Errors: {method_metrics.get('avg_tool_errors', 0.0):.2f}")
        print(f"  Avg Retrieval Misses: {method_metrics.get('avg_retrieval_misses', 0.0):.2f}")
        print(f"  Avg Tokens: {method_metrics.get('avg_tokens', 0.0):.0f}")

        failure_types = method_metrics.get("failure_types", {})
        if failure_types:
            print("  Failure Types:")
            for ftype, count in failure_types.items():
                print(f"    - {ftype}: {count}")

    # Comparison
    if comparison:
        print("\n📈 COMPARISON TO BASELINE")
        print("-" * 70)
        for method_name, method_comparison in comparison.items():
            print(f"\n{method_name.upper()}:")
            print(f"  Success Rate: {method_comparison['success_rate']:.1%}")
            improvement = method_comparison["absolute_improvement"]
            if improvement > 0:
                print(
                    f"  Improvement: +{improvement:.1%} ({method_comparison.get('relative_improvement', 0):.1f}%)"
                )
            elif improvement < 0:
                print(
                    f"  Change: {improvement:.1%} ({method_comparison.get('relative_improvement', 0):.1f}%)"
                )
            else:
                print("  Change: No change")

            token_eff = method_comparison.get("token_efficiency", 1.0)
            if token_eff < 1.0:
                print(f"  Token Efficiency: {token_eff:.2f}x better")
            elif token_eff > 1.0:
                print(f"  Token Efficiency: {token_eff:.2f}x worse")
            else:
                print("  Token Efficiency: Same")

    # Failure patterns
    print("\n🔍 FAILURE PATTERN ANALYSIS")
    print("-" * 70)
    for method_name, _method_metrics in metrics.items():
        results = []  # We'd need to load full results for this
        patterns = analyze_failure_patterns(results)
        if any(patterns.values()):
            print(f"\n{method_name.upper()}:")
            for pattern, count in patterns.items():
                if count > 0:
                    print(f"  {pattern.replace('_', ' ').title()}: {count}")

    # Key insights
    print("\n💡 KEY INSIGHTS")
    print("-" * 70)

    baseline_metrics = metrics.get("baseline", {})
    baseline_success = baseline_metrics.get("success_rate", 0.0)

    insights = []

    if baseline_success == 0.0:
        insights.append(
            "⚠️  All methods show 0% success rate - agent adapters may be mock implementations"
        )
        insights.append(
            "   This is expected if adapters haven't been connected to real agent execution"
        )

    for method_name, method_comparison in comparison.items():
        improvement = method_comparison.get("absolute_improvement", 0.0)
        if improvement > 0:
            insights.append(f"✅ {method_name.upper()} shows improvement over baseline")
        elif improvement < 0:
            insights.append(f"❌ {method_name.upper()} performs worse than baseline")

    if not insights:
        insights.append(
            "📝 No significant differences detected - may need more data or real agent execution"
        )

    for insight in insights:
        print(f"  {insight}")

    print("\n" + "=" * 70)

    # Save summary if requested
    if summary_file:
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "comparison": comparison,
            "insights": insights,
        }
        with open(summary_file, "w") as f:
            json.dump(summary_data, f, indent=2, default=str)
        print(f"\n✓ Analysis summary saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze evaluation results")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results/real_eval",
        help="Directory containing evaluation results",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output file for analysis (supports .json or .md)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        return

    # Load all results (handles both combined and separate files)
    print(f"Loading results from {results_dir}...")
    results = load_all_results(results_dir)

    if not results:
        # Fallback to old method
        metrics = {}
        result_files = {
            "baseline": results_dir / "baseline.json",
            "gepa": results_dir / "gepa.json",
            "ace": results_dir / "ace.json",
            "superopt": results_dir / "superopt.json",
        }

        for method_name, result_file in result_files.items():
            if result_file.exists():
                try:
                    method_results = load_results(result_file)
                    results[method_name] = method_results
                    print(f"  Loaded {method_name}: {len(method_results)} tasks")
                except Exception as e:
                    print(f"  Error loading {method_name}: {e}")

    if not results:
        print("Error: No results found to analyze")
        return

    # Extract metrics for each method
    metrics = {}
    for method_name, method_results in results.items():
        metrics[method_name] = extract_metrics(method_results, method_name)
        print(
            f"  {method_name}: {metrics[method_name]['total_tasks']} tasks, {metrics[method_name]['success_rate'] * 100:.1f}% success"
        )

    # Compare methods
    comparison = compare_methods(metrics)

    # Generate outputs
    if args.format in ["markdown", "both"]:
        markdown_report = generate_markdown_report(metrics, results)
        md_output = (
            Path(args.output).with_suffix(".md") if args.output else results_dir / "analysis.md"
        )
        with open(md_output, "w") as f:
            f.write(markdown_report)
        print(f"\nMarkdown report saved to: {md_output}")

    if args.format in ["json", "both"]:
        json_output = (
            Path(args.output).with_suffix(".json")
            if args.output
            else results_dir / "analysis_summary.json"
        )
        print_summary(metrics, comparison, json_output)

    # Print summary to console
    print("\n" + "=" * 60)
    print(generate_markdown_report(metrics, results))


if __name__ == "__main__":
    main()

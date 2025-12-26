"""
Evaluation Metrics for SuperOpt

Implements the evaluation dimensions described in the paper:
- Reliability: Reduction in repeated failures
- Stability: Persistence of improvements
- Efficiency: Resource usage
- Generalization: Transfer across tasks
"""

from typing import Any

from superopt.core.trace import ExecutionTrace
from superopt.optimizer import SuperOpt


class ReliabilityMetrics:
    """Metrics for measuring reliability improvements."""

    @staticmethod
    def compute_reliability(traces: list[ExecutionTrace]) -> float:
        """
        Compute reliability as: 1 - (repeated_failures / total_failures)

        A failure is considered repeated if its diagnostic signature matches
        a previously observed trace.
        """
        if not traces:
            return 1.0

        failure_signatures = {}
        repeated_failures = 0
        total_failures = 0

        for trace in traces:
            if not trace.success:
                total_failures += 1
                signature = ReliabilityMetrics._get_failure_signature(trace)

                if signature in failure_signatures:
                    repeated_failures += 1
                else:
                    failure_signatures[signature] = True

        if total_failures == 0:
            return 1.0

        return 1.0 - (repeated_failures / total_failures)

    @staticmethod
    def _get_failure_signature(trace: ExecutionTrace) -> str:
        """Generate a signature for a failure trace."""
        parts = []

        if trace.failure_type:
            parts.append(trace.failure_type.value)

        if trace.tool_errors:
            error_types = {e.error_message for e in trace.tool_errors if e.error_message}
            parts.append(f"tool_errors:{len(error_types)}")

        if trace.compiler_errors:
            parts.append(f"compiler_errors:{len(trace.compiler_errors)}")

        return "|".join(parts)


class StabilityMetrics:
    """Metrics for measuring stability of improvements."""

    @staticmethod
    def check_stability(optimizer: SuperOpt) -> dict[str, Any]:
        """
        Check if improvements persist without oscillation.

        Returns:
            Dictionary with stability indicators
        """
        history = optimizer.optimization_history

        # Check for contradictory updates
        contradictory_updates = 0
        for i in range(len(history) - 1):
            if StabilityMetrics._contradicts(history[i], history[i + 1]):
                contradictory_updates += 1

        # Check for reversion
        reversions = 0
        # This would require comparing environment states

        return {
            "contradictory_updates": contradictory_updates,
            "reversions": reversions,
            "total_updates": len(history),
            "stability_score": 1.0 - (contradictory_updates / max(len(history), 1)),
        }

    @staticmethod
    def _contradicts(update1: dict[str, Any], update2: dict[str, Any]) -> bool:
        """Check if two updates contradict each other."""
        # Simplified check - can be enhanced
        if update1.get("failure_type") == update2.get("failure_type"):
            # Same failure type might indicate oscillation
            return False  # Not necessarily contradictory
        return False


class EfficiencyMetrics:
    """Metrics for measuring efficiency improvements."""

    @staticmethod
    def compute_efficiency(traces: list[ExecutionTrace]) -> dict[str, float]:
        """
        Compute efficiency metrics.

        Returns:
            Dictionary with efficiency metrics
        """
        if not traces:
            return {}

        total_tokens = sum(t.token_count or 0 for t in traces)
        total_tool_calls = sum(len(t.tool_calls) for t in traces)
        total_retries = len([t for t in traces if not t.success])
        avg_duration = sum(t.duration_seconds or 0 for t in traces) / len(traces)

        return {
            "total_tokens": total_tokens,
            "avg_tokens_per_task": total_tokens / len(traces),
            "total_tool_calls": total_tool_calls,
            "avg_tool_calls_per_task": total_tool_calls / len(traces),
            "total_retries": total_retries,
            "avg_retries_per_task": total_retries / len(traces),
            "avg_duration_seconds": avg_duration,
        }


class GeneralizationMetrics:
    """Metrics for measuring generalization across tasks."""

    @staticmethod
    def compute_generalization(
        task_results: dict[str, list[ExecutionTrace]],
    ) -> dict[str, float]:
        """
        Compute generalization metrics across tasks.

        Args:
            task_results: Dictionary mapping task categories to traces

        Returns:
            Dictionary with generalization metrics
        """
        if not task_results:
            return {}

        # Compute success rate per task category
        category_success_rates = {}
        for category, traces in task_results.items():
            if traces:
                success_rate = sum(1 for t in traces if t.success) / len(traces)
                category_success_rates[category] = success_rate

        # Overall success rate
        all_traces = [t for traces in task_results.values() for t in traces]
        overall_success_rate = (
            sum(1 for t in all_traces if t.success) / len(all_traces) if all_traces else 0.0
        )

        # Variance in success rates (lower is better for generalization)
        if len(category_success_rates) > 1:
            success_rates = list(category_success_rates.values())
            mean_sr = sum(success_rates) / len(success_rates)
            variance = sum((sr - mean_sr) ** 2 for sr in success_rates) / len(success_rates)
        else:
            variance = 0.0

        return {
            "overall_success_rate": overall_success_rate,
            "category_success_rates": category_success_rates,
            "success_rate_variance": variance,
            "num_categories": len(category_success_rates),
        }

"""
Comparison Framework for SuperOpt vs GEPA vs ACE

Provides unified framework for running comparative experiments.
"""

from typing import Any

from superopt.adapters.base import AgentAdapter
from superopt.comparison.models import ModelConfig
from superopt.core.trace import ExecutionTrace


class ComparisonFramework:
    """
    Unified framework for comparing SuperOpt against GEPA and ACE.

    Ensures fair comparison by:
    - Using same task sets
    - Using same evaluation metrics
    - Using same computational budget
    - Using same agent base
    """

    def __init__(
        self,
        tasks: list[str],
        agent_adapter: AgentAdapter,
        superopt_optimizer,
        model_config: ModelConfig | None = None,
        gepa_adapter=None,
        ace_adapter=None,
    ):
        """
        Initialize comparison framework.

        Args:
            tasks: List of task descriptions
            agent_adapter: Agent adapter for executing tasks
            superopt_optimizer: SuperOpt optimizer instance
            model_config: Model configuration for fair comparison (optional)
            gepa_adapter: GEPA adapter (optional)
            ace_adapter: ACE adapter (optional)
        """
        self.tasks = tasks
        self.agent_adapter = agent_adapter
        self.superopt_optimizer = superopt_optimizer
        self.model_config = model_config
        self.gepa_adapter = gepa_adapter
        self.ace_adapter = ace_adapter

        self.results: dict[str, list[dict[str, Any]]] = {
            "baseline": [],
            "superopt": [],
            "gepa": [],
            "ace": [],
        }

    def run_baseline(self) -> list[dict[str, Any]]:
        """
        Run baseline (static agent, no optimization).

        Returns:
            List of task results
        """
        results = []
        baseline_env = self.agent_adapter.extract_environment()

        for task in self.tasks:
            trace = self.agent_adapter.execute(task, baseline_env)
            results.append(
                {
                    "task": task,
                    "trace": trace,
                    "success": trace.success,
                    "retries": self._count_retries(trace),
                    "tool_errors": len(trace.tool_errors),
                    "retrieval_misses": self._count_retrieval_misses(trace),
                    "tokens": trace.token_count or 0,
                }
            )

        self.results["baseline"] = results
        return results

    def run_superopt(self, max_iterations: int = 10) -> list[dict[str, Any]]:
        """
        Run SuperOpt optimization.

        Args:
            max_iterations: Maximum optimization iterations per task

        Returns:
            List of task results
        """
        if not self.superopt_optimizer:
            raise ValueError("SuperOpt optimizer not provided")

        results = []
        optimizer = self.superopt_optimizer

        for task in self.tasks:
            # Create agent executor function
            def agent_executor(task_desc: str, environment):
                return self.agent_adapter.execute(task_desc, environment)

            # Run optimization episode
            episode_results = optimizer.optimize_episode(
                task_description=task,
                agent_executor=agent_executor,
                max_iterations=max_iterations,
            )

            # Extract final trace from results
            # episode_results["traces"] contains dict representations
            from superopt.core.trace import ExecutionTrace

            final_trace = None
            if episode_results.get("traces"):
                # Reconstruct trace from dict (or use last trace if stored as objects)
                trace_dicts = episode_results["traces"]
                if trace_dicts:
                    final_trace = ExecutionTrace.from_dict(trace_dicts[-1])

            # Calculate metrics
            total_tool_errors = 0
            total_retrieval_misses = 0
            total_tokens = 0

            if episode_results.get("traces"):
                for trace_dict in trace_dicts:
                    trace = ExecutionTrace.from_dict(trace_dict)
                    total_tool_errors += len(trace.tool_errors)
                    total_retrieval_misses += self._count_retrieval_misses(trace)
                    total_tokens += trace.token_count or 0

            results.append(
                {
                    "task": task,
                    "trace": final_trace.to_dict() if final_trace else None,
                    "success": episode_results.get("success", False),
                    "retries": len(episode_results.get("traces", [])),
                    "tool_errors": total_tool_errors,
                    "retrieval_misses": total_retrieval_misses,
                    "tokens": total_tokens,
                    "optimization_steps": episode_results.get("iterations", 0),
                    "converged": episode_results.get("success", False),
                }
            )

        self.results["superopt"] = results
        return results

    def run_gepa(self) -> list[dict[str, Any]]:
        """
        Run GEPA prompt optimization.

        Returns:
            List of task results
        """
        if not self.gepa_adapter:
            raise ValueError("GEPA adapter not provided")

        # Ensure gepa_adapter has agent_adapter set (for optimization)
        if not self.gepa_adapter.agent_adapter:
            self.gepa_adapter.agent_adapter = self.agent_adapter

        # Get initial prompt from baseline environment
        baseline_env = self.agent_adapter.extract_environment()
        initial_prompt = baseline_env.prompts.system_prompt

        # Optimize prompts using GEPA
        gepa_prompts = self.gepa_adapter.optimize_prompts(
            tasks=self.tasks,
            initial_prompt=initial_prompt,
        )

        # Run tasks with GEPA-optimized prompts
        results = []
        # Create new environment with optimized prompt (don't mutate baseline)
        from dataclasses import replace

        gepa_env = replace(
            baseline_env,
            prompts=replace(
                baseline_env.prompts,
                system_prompt=gepa_prompts.get("system_prompt", initial_prompt),
            ),
        )

        for task in self.tasks:
            trace = self.agent_adapter.execute(task, gepa_env)
            results.append(
                {
                    "task": task,
                    "trace": trace,
                    "success": trace.success,
                    "retries": self._count_retries(trace),
                    "tool_errors": len(trace.tool_errors),
                    "retrieval_misses": self._count_retrieval_misses(trace),
                    "tokens": trace.token_count or 0,
                }
            )

        self.results["gepa"] = results
        return results

    def run_ace(self) -> list[dict[str, Any]]:
        """
        Run ACE context accumulation.

        Returns:
            List of task results
        """
        if not self.ace_adapter:
            raise ValueError("ACE adapter not provided")

        # Ensure ace_adapter has agent_adapter set (for evaluation if needed)
        if hasattr(self.ace_adapter, "agent_adapter") and not self.ace_adapter.agent_adapter:
            self.ace_adapter.agent_adapter = self.agent_adapter

        # Accumulate context using ACE
        ace_context = self.ace_adapter.accumulate_context(self.tasks)

        # Run tasks with ACE-accumulated context
        results = []
        baseline_env = self.agent_adapter.extract_environment()

        # Create environment with ACE context (don't mutate baseline)
        ace_env = self.ace_adapter.apply_context(baseline_env, ace_context)

        for task in self.tasks:
            # Use the ACE-enhanced environment
            trace = self.agent_adapter.execute(task, ace_env)
            results.append(
                {
                    "task": task,
                    "trace": trace,
                    "success": trace.success,
                    "retries": self._count_retries(trace),
                    "tool_errors": len(trace.tool_errors),
                    "retrieval_misses": self._count_retrieval_misses(trace),
                    "tokens": trace.token_count or 0,
                    "context_size": len(ace_context),
                }
            )

        self.results["ace"] = results
        return results

    def compare_all(self) -> dict[str, Any]:
        """
        Run all comparisons and return aggregated results.

        Returns:
            Dictionary with comparison results
        """
        baseline_results = self.run_baseline()
        superopt_results = self.run_superopt()

        gepa_results = None
        if self.gepa_adapter:
            gepa_results = self.run_gepa()

        ace_results = None
        if self.ace_adapter:
            ace_results = self.run_ace()

        return self._analyze_results(
            baseline_results,
            superopt_results,
            gepa_results,
            ace_results,
        )

    def _analyze_results(
        self,
        baseline: list[dict[str, Any]],
        superopt: list[dict[str, Any]],
        gepa: list[dict[str, Any]] | None,
        ace: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Analyze and compare results."""
        analysis = {
            "baseline": self._compute_metrics(baseline),
            "superopt": self._compute_metrics(superopt),
        }

        if gepa:
            analysis["gepa"] = self._compute_metrics(gepa)
            analysis["superopt_vs_gepa"] = self._compare_metrics(
                analysis["superopt"],
                analysis["gepa"],
            )

        if ace:
            analysis["ace"] = self._compute_metrics(ace)
            analysis["superopt_vs_ace"] = self._compare_metrics(
                analysis["superopt"],
                analysis["ace"],
            )

        return analysis

    def _compute_metrics(self, results: list[dict[str, Any]]) -> dict[str, float]:
        """Compute aggregate metrics from results."""
        if not results:
            return {}

        total_tasks = len(results)
        successful_tasks = sum(1 for r in results if r["success"])

        return {
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0.0,
            "avg_retries": sum(r["retries"] for r in results) / total_tasks
            if total_tasks > 0
            else 0.0,
            "avg_tool_errors": sum(r["tool_errors"] for r in results) / total_tasks
            if total_tasks > 0
            else 0.0,
            "avg_retrieval_misses": sum(r["retrieval_misses"] for r in results) / total_tasks
            if total_tasks > 0
            else 0.0,
            "avg_tokens": sum(r["tokens"] for r in results) / total_tasks
            if total_tasks > 0
            else 0.0,
        }

    def _compare_metrics(
        self,
        metrics1: dict[str, float],
        metrics2: dict[str, float],
    ) -> dict[str, float]:
        """Compare two metric sets and compute relative differences."""
        comparison = {}
        for key in metrics1:
            if key in metrics2 and metrics2[key] != 0:
                relative_change = (metrics1[key] - metrics2[key]) / metrics2[key]
                comparison[key] = relative_change
        return comparison

    def _count_retries(self, trace: ExecutionTrace) -> int:
        """Count retries in a trace."""
        # Simple heuristic: count tool errors as retries
        return len(trace.tool_errors)

    def _count_retrieval_misses(self, trace: ExecutionTrace) -> int:
        """Count retrieval misses in a trace."""
        empty_queries = sum(1 for q in trace.retrieval_queries if len(q.retrieved_documents) == 0)
        return empty_queries

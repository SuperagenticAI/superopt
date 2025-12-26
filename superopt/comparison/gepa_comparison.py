"""
GEPA Comparison Adapter

Integrates GEPA for prompt optimization to compare against SuperOpt.
"""

from typing import Any

from superopt.adapters.base import AgentAdapter
from superopt.comparison.gepa_adapter import AgentDataInst, AgentGEPAAdapter
from superopt.comparison.models import ModelConfig


class GEPAComparison:
    """
    Adapter for comparing SuperOpt against GEPA.

    GEPA optimizes prompts only, so this adapter:
    1. Uses GEPA to optimize prompts
    2. Runs tasks with GEPA-optimized prompts
    3. Compares against SuperOpt (which optimizes full environment)
    """

    def __init__(
        self,
        agent_adapter: AgentAdapter | None = None,
        model_config: ModelConfig | None = None,
        api_base: str | None = None,
    ):
        """
        Initialize GEPA comparison adapter.

        Args:
            agent_adapter: Agent adapter for executing tasks (required for optimization)
            model_config: Model configuration (optional)
            api_base: API base URL for models (optional, for Ollama)
        """
        self.agent_adapter = agent_adapter
        self.model_config = model_config
        self.api_base = api_base
        self.optimized_prompts: dict[str, str] | None = None
        self.gepa_result = None

    def optimize_prompts(
        self,
        tasks: list[str],
        initial_prompt: str = "",
        max_metric_calls: int = 150,
    ) -> dict[str, str]:
        """
        Optimize prompts using GEPA.

        Args:
            tasks: List of task descriptions
            initial_prompt: Initial system prompt
            max_metric_calls: Maximum number of metric evaluations (budget)

        Returns:
            Dictionary with optimized prompt components
        """
        if not self.agent_adapter:
            # Return initial prompt if agent adapter not available
            return {"system_prompt": initial_prompt}

        try:
            import gepa
        except ImportError:
            raise ImportError("GEPA is not installed. Install with: pip install gepa")

        try:
            # Convert tasks to GEPA format (AgentDataInst)
            gepa_tasks = [AgentDataInst(input=task, expected_output=None) for task in tasks]

            # Split into train/val sets
            split_idx = len(gepa_tasks) * 2 // 3
            trainset = gepa_tasks[:split_idx]
            valset = gepa_tasks[split_idx:]

            # Create GEPA adapter for agent execution
            agent_gepa_adapter = AgentGEPAAdapter(
                agent_adapter=self.agent_adapter,
                model_config=self.model_config,
                failure_score=0.0,
            )

            # Determine model names
            task_lm = self.model_config.task_model if self.model_config else "ollama/gpt-oss:20b"
            reflection_lm = (
                self.model_config.reflection_model if self.model_config else "ollama/gpt-oss:120b"
            )

            # Set API base for Ollama (use provided api_base or from model_config)
            import os

            if self.model_config and self.model_config.provider.value == "ollama":
                api_base = self.api_base or self.model_config.api_base
                if api_base:
                    os.environ["OLLAMA_API_BASE"] = api_base
                elif "OLLAMA_API_BASE" not in os.environ:
                    # Set default Ollama API base if not already set
                    os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"
            elif self.api_base:
                # Fallback: set if explicitly provided
                os.environ["OLLAMA_API_BASE"] = self.api_base

            # Run GEPA optimization
            gepa_result = gepa.optimize(
                seed_candidate={"system_prompt": initial_prompt},
                trainset=trainset,
                valset=valset,
                adapter=agent_gepa_adapter,
                task_lm=task_lm,
                reflection_lm=reflection_lm,
                max_metric_calls=max_metric_calls,
                candidate_selection_strategy="pareto",
                display_progress_bar=True,
            )

            # Extract best candidate
            self.gepa_result = gepa_result
            self.optimized_prompts = gepa_result.best_candidate

            return self.optimized_prompts

        except Exception as e:
            # Fallback to initial prompt on error
            import warnings

            warnings.warn(
                f"GEPA optimization failed: {e}. Using initial prompt.",
                UserWarning,
            )
            self.optimized_prompts = {"system_prompt": initial_prompt}
            return self.optimized_prompts

    def get_optimized_prompt(self) -> str:
        """Get the optimized prompt."""
        if self.optimized_prompts:
            return self.optimized_prompts.get("system_prompt", "")
        return ""

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get GEPA optimization statistics."""
        if not self.gepa_result:
            return {}

        return {
            "total_metric_calls": self.gepa_result.total_metric_calls or 0,
            "best_score": getattr(self.gepa_result, "best_score", None),
            "pareto_front_size": len(self.gepa_result.pareto_front)
            if hasattr(self.gepa_result, "pareto_front")
            else 0,
        }

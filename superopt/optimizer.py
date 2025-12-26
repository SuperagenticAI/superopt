"""
SuperOpt: Main Optimization Framework

The integrated SuperOpt system that coordinates all components:
- SuperController for diagnosis
- SuperPrompt for prompt evolution
- SuperReflexion for tool repair
- SuperRAG for retrieval optimization
- SuperMem for memory management
"""

from typing import Any

from superopt.core.environment import AgenticEnvironment
from superopt.core.trace import ExecutionTrace, FailureType
from superopt.stability import MutabilityHierarchy
from superopt.supercontroller import SuperController
from superopt.supermem import SuperMem
from superopt.superprompt import SuperPrompt
from superopt.superrag import SuperRAG
from superopt.superreflexion import SuperReflexion


class SuperOpt:
    """
    Main SuperOpt optimizer.

    Coordinates the full optimization loop:
    1. Execute agent task
    2. Capture execution trace
    3. Diagnose failure mode
    4. Route to specialized optimizer
    5. Generate environment update
    6. Validate against stability constraints
    7. Apply update
    """

    def __init__(
        self,
        environment: AgenticEnvironment | None = None,
        llm_client=None,
        alpha: float = 1.0,
        use_stability_checks: bool = True,
    ):
        """
        Initialize SuperOpt.

        Args:
            environment: Initial agentic environment
            llm_client: LLM client for optimizers (optional)
            alpha: Update acceptance rate (0.0 to 1.0)
            use_stability_checks: Whether to enforce stability constraints
        """
        self.environment = environment or AgenticEnvironment()
        self.alpha = alpha
        self.use_stability_checks = use_stability_checks

        # Initialize components
        self.controller = SuperController(use_llm_diagnosis=False, llm_client=llm_client)
        self.superprompt = SuperPrompt(llm_client=llm_client)
        self.superreflexion = SuperReflexion(llm_client=llm_client)
        self.superrag = SuperRAG()
        self.supermem = SuperMem()

        # History
        self.optimization_history: list[dict[str, Any]] = []

    def step(self, trace: ExecutionTrace) -> "SuperOpt":
        """
        Perform one optimization step based on execution trace.

        Args:
            trace: Execution trace from agent execution

        Returns:
            Self for method chaining
        """
        # Diagnose failure type
        failure_type = self.controller.diagnose(trace, self.environment)

        # Generate Natural Language Gradient based on failure type
        nlg = None

        if failure_type == FailureType.PROMPT:
            nlg = self.superprompt.optimize(self.environment, trace)

        elif failure_type == FailureType.TOOL:
            nlg = self.superreflexion.repair(self.environment, trace)

        elif failure_type == FailureType.RETRIEVAL:
            nlg = self.superrag.adapt(self.environment, trace)

        elif failure_type == FailureType.MEMORY:
            nlg = self.supermem.update(self.environment, trace)

        # Apply update if valid
        if nlg and not nlg.is_empty():
            if self.use_stability_checks:
                # Validate against hierarchy
                is_valid, error = MutabilityHierarchy.validate_update(nlg, self.environment)
                if not is_valid:
                    # Log rejection
                    self.optimization_history.append(
                        {
                            "trace_id": trace.task_id,
                            "failure_type": failure_type.value,
                            "update_rejected": True,
                            "reason": error,
                        }
                    )
                    return self

            # Apply update
            if self.use_stability_checks:
                self.environment = MutabilityHierarchy.apply_with_hierarchy(
                    self.environment,
                    nlg,
                    self.alpha,
                )
            else:
                self.environment = self.environment.apply_update(nlg, self.alpha)

            # Record update
            self.optimization_history.append(
                {
                    "trace_id": trace.task_id,
                    "failure_type": failure_type.value,
                    "update_applied": True,
                    "nlg": nlg.to_dict(),
                }
            )

        return self

    def optimize_episode(
        self,
        task_description: str,
        agent_executor,
        max_iterations: int = 10,
    ) -> dict[str, Any]:
        """
        Optimize environment over a full episode of agent execution.

        Args:
            task_description: Description of the task
            agent_executor: Callable that executes agent and returns trace
            max_iterations: Maximum optimization iterations

        Returns:
            Dictionary with optimization results
        """
        iteration = 0
        traces = []

        while iteration < max_iterations:
            # Execute agent
            trace = agent_executor(task_description, self.environment)
            traces.append(trace)

            # Optimize based on trace
            self.step(trace)

            # Check convergence
            if trace.success:
                break

            iteration += 1

        return {
            "success": traces[-1].success if traces else False,
            "iterations": iteration + 1,
            "traces": [t.to_dict() for t in traces],
            "final_environment": self.environment.to_dict(),
            "optimization_history": self.optimization_history,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get optimization statistics."""
        return {
            "controller_stats": self.controller.get_statistics(),
            "optimization_steps": len(self.optimization_history),
            "environment_snapshot": self.environment.to_dict(),
        }

    def reset(self, new_environment: AgenticEnvironment | None = None):
        """Reset optimizer state."""
        if new_environment:
            self.environment = new_environment
        else:
            self.environment = AgenticEnvironment()

        self.optimization_history = []
        self.controller.reset_statistics()

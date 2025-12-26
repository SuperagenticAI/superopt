"""
SuperPrompt: Evolutionary Instruction Optimization

SuperPrompt optimizes system prompts using evolutionary search with
Pareto objectives, building on GEPA principles but integrated into
the broader SuperOpt framework.
"""

import copy
from typing import Any

from superopt.core.environment import AgenticEnvironment, PromptConfig
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace


class PromptCandidate:
    """A candidate prompt configuration for evolutionary search."""

    def __init__(self, prompt: PromptConfig, scores: dict[str, float] | None = None):
        self.prompt = prompt
        self.scores = scores or {}

    def dominates(self, other: "PromptCandidate") -> bool:
        """
        Check if this candidate dominates another (Pareto dominance).

        A candidate dominates if it's better or equal in all objectives
        and strictly better in at least one.
        """
        if not self.scores or not other.scores:
            return False

        better_in_any = False
        for metric in self.scores:
            if metric not in other.scores:
                continue
            if self.scores[metric] < other.scores[metric]:
                return False  # Worse in at least one metric
            if self.scores[metric] > other.scores[metric]:
                better_in_any = True

        return better_in_any


class SuperPrompt:
    """
    Evolutionary prompt optimizer.

    Maintains a population of candidate prompts and evolves them using:
    - Reflective mutation guided by execution traces
    - Pareto-based selection
    - Multi-objective evaluation (success rate, token efficiency, stability)
    """

    def __init__(
        self,
        population_size: int = 5,
        llm_client=None,
        objectives: list[str] | None = None,
    ):
        """
        Initialize SuperPrompt.

        Args:
            population_size: Number of prompt candidates to maintain
            llm_client: LLM client for generating mutations
            objectives: List of objective names (default: ["success_rate", "token_efficiency"])
        """
        self.population_size = population_size
        self.llm_client = llm_client
        self.objectives = objectives or ["success_rate", "token_efficiency"]
        self.population: list[PromptCandidate] = []
        self.evaluation_history: list[dict[str, Any]] = []

    def evolve(
        self,
        prompt_population: list[PromptConfig],
        trace: ExecutionTrace,
    ) -> list[PromptConfig]:
        """
        Evolve prompt population based on execution trace.

        Args:
            prompt_population: Current population of prompts
            trace: Execution trace with feedback

        Returns:
            Updated population of prompts (Pareto frontier)
        """
        # Convert to candidates
        candidates = [PromptCandidate(prompt) for prompt in prompt_population]

        # Generate mutations
        mutated_candidates = []
        for candidate in candidates:
            mutations = self.reflective_mutate(candidate.prompt, trace)
            mutated_candidates.extend([PromptCandidate(m) for m in mutations])

        # Evaluate candidates
        evaluated_candidates = []
        for candidate in mutated_candidates + candidates:
            scores = self.evaluate(candidate.prompt, trace)
            candidate.scores = scores
            evaluated_candidates.append(candidate)

        # Select Pareto frontier
        pareto_front = self.select_pareto_front(evaluated_candidates)

        # Limit to population size
        if len(pareto_front) > self.population_size:
            pareto_front = pareto_front[: self.population_size]

        # Convert back to prompts
        return [candidate.prompt for candidate in pareto_front]

    def optimize(
        self,
        environment: AgenticEnvironment,
        trace: ExecutionTrace,
    ) -> NaturalLanguageGradient:
        """
        Optimize prompts and generate Natural Language Gradient.

        Args:
            environment: Current environment
            trace: Execution trace

        Returns:
            Natural Language Gradient with prompt updates
        """
        # Initialize population if empty
        if not self.population:
            self.population = [PromptCandidate(environment.prompts)]

        # Evolve population
        current_prompts = [c.prompt for c in self.population]
        evolved_prompts = self.evolve(current_prompts, trace)

        # Select best prompt (highest success rate)
        best_prompt = max(
            evolved_prompts,
            key=lambda p: self._get_best_score(p, trace),
        )

        # Compute delta
        delta_p = self._compute_prompt_delta(environment.prompts, best_prompt)

        # Update population
        self.population = [PromptCandidate(p) for p in evolved_prompts]

        return NaturalLanguageGradient(
            delta_p=delta_p,
            source_trace_id=trace.task_id,
        )

    def reflective_mutate(
        self,
        prompt: PromptConfig,
        trace: ExecutionTrace,
        num_candidates: int = 3,
    ) -> list[PromptConfig]:
        """
        Generate reflective mutations of a prompt based on failure trace.

        Args:
            prompt: Base prompt to mutate
            trace: Execution trace with failure information
            num_candidates: Number of mutation candidates to generate

        Returns:
            List of mutated prompt configurations
        """
        if self.llm_client:
            return self._llm_mutate(prompt, trace, num_candidates)
        else:
            return self._rule_based_mutate(prompt, trace, num_candidates)

    def _rule_based_mutate(
        self,
        prompt: PromptConfig,
        trace: ExecutionTrace,
        num_candidates: int,
    ) -> list[PromptConfig]:
        """Generate mutations using rule-based approach."""
        mutations = []

        # Extract failure patterns
        failures = self._extract_prompt_failures(trace)

        for _i in range(num_candidates):
            new_prompt = copy.deepcopy(prompt)

            # Add constraints based on failures
            if "format_error" in failures:
                new_prompt.behavioral_constraints.append(
                    "CRITICAL: Follow the exact output format specification."
                )

            if "instruction_violation" in failures:
                new_prompt.instruction_policy += (
                    "\n\nIMPORTANT: Strictly adhere to all instructions above."
                )

            if "tool_misuse" in failures:
                new_prompt.behavioral_constraints.append(
                    "CRITICAL: Verify tool arguments match schemas exactly before invocation."
                )

            mutations.append(new_prompt)

        return mutations

    def _llm_mutate(
        self,
        prompt: PromptConfig,
        trace: ExecutionTrace,
        num_candidates: int,
    ) -> list[PromptConfig]:
        """Generate mutations using LLM."""
        if not self.llm_client:
            return self._rule_based_mutate(prompt, trace, num_candidates)

        prompt_text = self._build_mutation_prompt(prompt, trace)

        try:
            response = self.llm_client.generate(prompt_text)
            # Parse response to extract prompt updates
            mutations = self._parse_mutation_response(response, prompt, num_candidates)
            return mutations
        except Exception:
            return self._rule_based_mutate(prompt, trace, num_candidates)

    def evaluate(self, prompt: PromptConfig, trace: ExecutionTrace) -> dict[str, float]:
        """
        Evaluate a prompt candidate on multiple objectives.

        Args:
            prompt: Prompt to evaluate
            trace: Execution trace

        Returns:
            Dictionary of objective scores
        """
        scores = {}

        # Success rate (based on trace success)
        scores["success_rate"] = 1.0 if trace.success else 0.0

        # Token efficiency (inverse of token count)
        if trace.token_count:
            scores["token_efficiency"] = 1.0 / (1.0 + trace.token_count / 1000.0)
        else:
            scores["token_efficiency"] = 0.5

        # Stability (based on repeated errors)
        if trace.repeats_known_mistake():
            scores["stability"] = 0.0
        else:
            scores["stability"] = 1.0

        # Tool error reduction
        if trace.tool_errors:
            scores["tool_compliance"] = 1.0 / (1.0 + len(trace.tool_errors))
        else:
            scores["tool_compliance"] = 1.0

        return scores

    def select_pareto_front(self, candidates: list[PromptCandidate]) -> list[PromptCandidate]:
        """
        Select Pareto-optimal candidates.

        Returns:
            List of non-dominated candidates
        """
        if not candidates:
            return []

        pareto_front = []

        for candidate in candidates:
            dominated = False
            for other in candidates:
                if other.dominates(candidate):
                    dominated = True
                    break

            if not dominated:
                pareto_front.append(candidate)

        # Sort by primary objective (success_rate)
        pareto_front.sort(
            key=lambda c: c.scores.get("success_rate", 0.0),
            reverse=True,
        )

        return pareto_front

    def _extract_prompt_failures(self, trace: ExecutionTrace) -> list[str]:
        """Extract prompt-related failure patterns from trace."""
        failures = []

        if trace.output_format_error():
            failures.append("format_error")

        if trace.violates_instruction():
            failures.append("instruction_violation")

        if trace.tool_errors:
            failures.append("tool_misuse")

        return failures

    def _compute_prompt_delta(
        self,
        old_prompt: PromptConfig,
        new_prompt: PromptConfig,
    ) -> dict[str, Any]:
        """Compute delta between old and new prompts."""
        delta = {}

        # Check for additions
        new_constraints = [
            c
            for c in new_prompt.behavioral_constraints
            if c not in old_prompt.behavioral_constraints
        ]
        if new_constraints:
            delta["new_constraints"] = new_constraints

        # Check for prompt additions
        if new_prompt.system_prompt != old_prompt.system_prompt:
            additions = new_prompt.system_prompt[len(old_prompt.system_prompt) :].strip()
            if additions:
                delta["additions"] = additions

        # Check for new exemplars
        new_exemplars = [
            e for e in new_prompt.few_shot_exemplars if e not in old_prompt.few_shot_exemplars
        ]
        if new_exemplars:
            delta["new_exemplars"] = new_exemplars

        return delta

    def _get_best_score(self, prompt: PromptConfig, trace: ExecutionTrace) -> float:
        """Get the best (primary) score for a prompt."""
        scores = self.evaluate(prompt, trace)
        return scores.get("success_rate", 0.0)

    def _build_mutation_prompt(
        self,
        prompt: PromptConfig,
        trace: ExecutionTrace,
    ) -> str:
        """Build prompt for LLM-based mutation."""
        return f"""Given this prompt and failure trace, generate improved prompt mutations.

Current Prompt:
{prompt.system_prompt}

Failure Trace:
{trace.summary()}

Generate {3} improved versions that address the failures while maintaining clarity.
"""

    def _parse_mutation_response(
        self,
        response: str,
        base_prompt: PromptConfig,
        num_candidates: int,
    ) -> list[PromptConfig]:
        """Parse LLM response to extract prompt mutations."""
        # Simple implementation - can be enhanced
        mutations = []
        for i in range(num_candidates):
            new_prompt = copy.deepcopy(base_prompt)
            new_prompt.system_prompt += f"\n\n[Mutation {i + 1} improvements based on feedback]"
            mutations.append(new_prompt)
        return mutations

"""
SuperController: Diagnostic Meta-Controller

The SuperController analyzes execution traces and determines where in the
environment a failure originated. It routes failures to appropriate
optimization engines.
"""

from superopt.core.environment import AgenticEnvironment
from superopt.core.trace import ExecutionTrace, FailureType


class SuperController:
    """
    Diagnostic meta-controller for failure attribution and routing.

    The controller classifies failures into diagnostic categories:
    - PROMPT: Instruction ignored, output format violation, hallucinated reasoning
    - TOOL: Invalid arguments, schema violation, runtime exception
    - RETRIEVAL: Missing symbols, hallucinated files, context overflow
    - MEMORY: Repetition of mistakes, contradictory rules, stale knowledge
    """

    def __init__(self, use_llm_diagnosis: bool = False, llm_client=None):
        """
        Initialize SuperController.

        Args:
            use_llm_diagnosis: Whether to use LLM-based diagnosis (vs rule-based)
            llm_client: LLM client for advanced diagnosis (optional)
        """
        self.use_llm_diagnosis = use_llm_diagnosis
        self.llm_client = llm_client
        self.failure_statistics: dict[str, int] = {
            "PROMPT": 0,
            "TOOL": 0,
            "RETRIEVAL": 0,
            "MEMORY": 0,
            "NONE": 0,
        }

    def diagnose(
        self, trace: ExecutionTrace, environment: AgenticEnvironment | None = None
    ) -> FailureType:
        """
        Classify the dominant failure mode in an execution trace.

        Args:
            trace: Execution trace to analyze
            environment: Current environment (optional, for context)

        Returns:
            FailureType enum indicating the dominant failure category
        """
        if self.use_llm_diagnosis and self.llm_client:
            failure_type = self._llm_diagnose(trace, environment)
        else:
            failure_type = self._rule_based_diagnose(trace)

        # Update statistics
        self.failure_statistics[failure_type.value] += 1

        return failure_type

    def _rule_based_diagnose(self, trace: ExecutionTrace) -> FailureType:
        """
        Rule-based diagnostic algorithm.

        Priority order:
        1. Tool errors (most specific)
        2. Retrieval failures
        3. Prompt violations
        4. Memory issues (default fallback)
        """
        # Check for tool-level failures
        if trace.has_tool_error() or trace.invalid_arguments():
            return FailureType.TOOL

        # Check for retrieval-level failures
        if trace.missing_symbol() or trace.retrieval_empty():
            return FailureType.RETRIEVAL

        # Check for prompt-level failures
        if trace.violates_instruction() or trace.output_format_error():
            return FailureType.PROMPT

        # Check for memory-level failures
        if trace.repeats_known_mistake() or trace.conflicts_with_memory():
            return FailureType.MEMORY

        # If trace succeeded, return NONE
        if trace.success:
            return FailureType.NONE

        # Default fallback to memory (most general)
        return FailureType.MEMORY

    def _llm_diagnose(
        self, trace: ExecutionTrace, environment: AgenticEnvironment | None = None
    ) -> FailureType:
        """
        LLM-based diagnostic algorithm.

        Uses an LLM to analyze the trace and classify the failure.
        Falls back to rule-based if LLM fails.
        """
        if not self.llm_client:
            return self._rule_based_diagnose(trace)

        # Build prompt for LLM diagnosis
        prompt = self._build_diagnosis_prompt(trace, environment)

        try:
            response = self.llm_client.generate(prompt)
            # Parse response to extract failure type
            failure_type_str = self._parse_llm_response(response)
            return FailureType(failure_type_str)
        except Exception:
            # Fallback to rule-based
            return self._rule_based_diagnose(trace)

    def _build_diagnosis_prompt(
        self, trace: ExecutionTrace, environment: AgenticEnvironment | None = None
    ) -> str:
        """Build prompt for LLM-based diagnosis."""
        prompt = f"""Analyze this execution trace and classify the dominant failure mode.

Execution Trace Summary:
{trace.summary()}

Available failure types:
- PROMPT: Instruction ignored, output format violation, hallucinated reasoning
- TOOL: Invalid arguments, schema violation, runtime exception
- RETRIEVAL: Missing symbols, hallucinated files, context overflow
- MEMORY: Repetition of mistakes, contradictory rules, stale knowledge
- NONE: No failure (successful execution)

Respond with only the failure type (e.g., "TOOL").
"""
        return prompt

    def _parse_llm_response(self, response: str) -> str:
        """Parse LLM response to extract failure type."""
        response = response.strip().upper()
        # Extract first valid failure type found
        for failure_type in ["PROMPT", "TOOL", "RETRIEVAL", "MEMORY", "NONE"]:
            if failure_type in response:
                return failure_type
        # Default fallback
        return "MEMORY"

    def get_statistics(self) -> dict[str, int]:
        """Get failure diagnosis statistics."""
        return self.failure_statistics.copy()

    def reset_statistics(self):
        """Reset failure statistics."""
        self.failure_statistics = {
            "PROMPT": 0,
            "TOOL": 0,
            "RETRIEVAL": 0,
            "MEMORY": 0,
            "NONE": 0,
        }

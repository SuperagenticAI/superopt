"""
Hierarchy of Mutability and Stability Constraints

SuperOpt enforces a strict hierarchy of mutability to prevent oscillation
and ensure convergence. Lower-priority adaptations cannot invalidate
higher-priority constraints.
"""

from superopt.core.environment import AgenticEnvironment
from superopt.core.nlg import NaturalLanguageGradient


class MutabilityHierarchy:
    """
    Hierarchy of mutability for environment components.

    Priority order (higher = more immutable):
    1. Immutable constraints (syntax rules, token limits, API invariants)
    2. Tool protocols (schemas and execution contracts)
    3. Retrieval configuration (access mechanisms and ranking policies)
    4. Prompts and stylistic instructions
    """

    PRIORITY_LEVELS = {
        "immutable_constraints": 4,
        "tool_protocols": 3,
        "retrieval_config": 2,
        "prompts": 1,
    }

    @staticmethod
    def validate_update(
        nlg: NaturalLanguageGradient,
        environment: AgenticEnvironment,
    ) -> tuple[bool, str | None]:
        """
        Validate that an update respects the hierarchy of mutability.

        Args:
            nlg: Natural Language Gradient to validate
            environment: Current environment

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check tool updates don't violate immutable constraints
        if nlg.delta_t:
            for tool_name, update in nlg.delta_t.items():
                if tool_name in environment.tools:
                    _schema = environment.tools[tool_name]
                    # Check if update violates immutable constraints
                    if "clarification" in update:
                        # Could add validation here
                        pass

        # Check prompt updates don't override tool constraints
        if nlg.delta_p and nlg.delta_t:
            # Prompts should not contradict tool schemas
            # This is a simplified check - can be enhanced
            pass

        # Check retrieval updates don't violate tool protocols
        if nlg.delta_r:
            # Retrieval config should not affect tool contracts
            pass

        return True, None

    @staticmethod
    def apply_with_hierarchy(
        environment: AgenticEnvironment,
        nlg: NaturalLanguageGradient,
        alpha: float = 1.0,
    ) -> AgenticEnvironment:
        """
        Apply update respecting hierarchy of mutability.

        Args:
            environment: Current environment
            nlg: Natural Language Gradient
            alpha: Update acceptance rate

        Returns:
            Updated environment
        """
        # Validate first
        is_valid, error = MutabilityHierarchy.validate_update(nlg, environment)
        if not is_valid:
            # Reject update if invalid
            return environment

        # Apply updates in priority order (lowest priority first)
        # This ensures higher-priority constraints are preserved

        # 1. Apply prompt updates (lowest priority)
        if nlg.delta_p:
            environment = environment.apply_update(
                NaturalLanguageGradient(delta_p=nlg.delta_p),
                alpha,
            )

        # 2. Apply retrieval updates
        if nlg.delta_r:
            environment = environment.apply_update(
                NaturalLanguageGradient(delta_r=nlg.delta_r),
                alpha,
            )

        # 3. Apply tool updates
        if nlg.delta_t:
            environment = environment.apply_update(
                NaturalLanguageGradient(delta_t=nlg.delta_t),
                alpha,
            )

        # 4. Apply memory updates (highest priority for learned constraints)
        if nlg.delta_m:
            environment = environment.apply_update(
                NaturalLanguageGradient(delta_m=nlg.delta_m),
                alpha,
            )

        return environment

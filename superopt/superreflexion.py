"""
SuperReflexion: Self-Healing Tool Schemas

SuperReflexion modifies tool definitions themselves when agents misuse tools.
Unlike prompt-based scolding, SuperReflexion repairs the environment by
clarifying tool schemas and adding explicit constraints.
"""

from typing import Any

from superopt.core.environment import AgenticEnvironment, ToolSchema
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace


class SuperReflexion:
    """
    Tool schema repair engine.

    When tool errors occur, SuperReflexion:
    1. Analyzes the tool failure
    2. Extracts the intended behavior vs actual behavior
    3. Generates schema clarifications
    4. Appends constraints to tool descriptions
    """

    def __init__(self, llm_client=None):
        """
        Initialize SuperReflexion.

        Args:
            llm_client: LLM client for generating schema patches (optional)
        """
        self.llm_client = llm_client
        self.patch_history: list = []

    def patch_schema(self, schema: ToolSchema, trace: ExecutionTrace) -> ToolSchema:
        """
        Generate a patch for a tool schema based on execution trace.

        Args:
            schema: Original tool schema
            trace: Execution trace containing tool errors

        Returns:
            Updated tool schema with clarifications
        """
        # Find relevant tool errors
        tool_errors = [error for error in trace.tool_errors if error.tool_name == schema.name]

        if not tool_errors:
            return schema

        # Analyze the failure
        diagnosis = self._analyze_tool_failure(tool_errors, schema)

        # Generate clarification
        clarification = self._generate_clarification(diagnosis, schema)

        # Create updated schema
        updated_schema = ToolSchema(
            name=schema.name,
            description=schema.description + "\n\n" + clarification,
            arguments=schema.arguments.copy(),
            required_fields=schema.required_fields.copy(),
            constraints=schema.constraints + diagnosis.get("new_constraints", []),
            examples=schema.examples.copy(),
        )

        # Record patch
        self.patch_history.append(
            {
                "tool_name": schema.name,
                "clarification": clarification,
                "trace_id": trace.task_id,
            }
        )

        return updated_schema

    def repair(
        self, environment: AgenticEnvironment, trace: ExecutionTrace
    ) -> NaturalLanguageGradient:
        """
        Repair tool schemas based on execution trace.

        Args:
            environment: Current environment
            trace: Execution trace with tool errors

        Returns:
            Natural Language Gradient with tool updates
        """
        delta_t = {}

        # Process each tool error
        for error in trace.tool_errors:
            tool_name = error.tool_name
            if tool_name in environment.tools:
                schema = environment.tools[tool_name]
                patched_schema = self.patch_schema(schema, trace)

                # Extract the clarification (new part added)
                original_desc = schema.description
                new_desc = patched_schema.description
                clarification = new_desc[len(original_desc) :].strip()

                delta_t[tool_name] = {
                    "clarification": clarification,
                    "new_constraints": patched_schema.constraints[len(schema.constraints) :],
                }

        return NaturalLanguageGradient(
            delta_t=delta_t if delta_t else None,
            source_trace_id=trace.task_id,
        )

    def _analyze_tool_failure(self, tool_errors: list, schema: ToolSchema) -> dict[str, Any]:
        """
        Analyze tool failures to extract patterns.

        Returns:
            Dictionary with diagnosis and suggested fixes
        """
        diagnosis = {
            "error_patterns": [],
            "missing_constraints": [],
            "new_constraints": [],
        }

        for error in tool_errors:
            error_msg = error.error_message or ""
            error_msg_lower = error_msg.lower()

            # Common error patterns
            if "index" in error_msg_lower or "line" in error_msg_lower:
                if "0" in error_msg or "zero" in error_msg_lower:
                    diagnosis["new_constraints"].append(
                        "CRITICAL: Line numbers and indices are 1-indexed, not 0-indexed."
                    )

            if "invalid" in error_msg_lower and "argument" in error_msg_lower:
                diagnosis["new_constraints"].append(
                    "CRITICAL: Verify argument types match the schema exactly."
                )

            if "required" in error_msg_lower or "missing" in error_msg_lower:
                diagnosis["missing_constraints"].append(
                    "CRITICAL: All required fields must be provided."
                )

            if "format" in error_msg_lower or "syntax" in error_msg_lower:
                diagnosis["new_constraints"].append(
                    "CRITICAL: Follow the exact format specification in the schema."
                )

        return diagnosis

    def _generate_clarification(self, diagnosis: dict[str, Any], schema: ToolSchema) -> str:
        """
        Generate natural language clarification for tool schema.

        Args:
            diagnosis: Failure analysis
            schema: Tool schema

        Returns:
            Clarification text to append to schema description
        """
        if self.llm_client:
            return self._llm_generate_clarification(diagnosis, schema)
        else:
            return self._rule_based_clarification(diagnosis, schema)

    def _rule_based_clarification(self, diagnosis: dict[str, Any], schema: ToolSchema) -> str:
        """Generate clarification using rule-based approach."""
        parts = ["**IMPORTANT CONSTRAINTS:**"]

        # Add new constraints
        for constraint in diagnosis.get("new_constraints", []):
            parts.append(f"- {constraint}")

        # Add common clarifications based on error patterns
        if diagnosis.get("missing_constraints"):
            parts.append("- Ensure all required fields are provided before invocation.")

        return "\n".join(parts)

    def _llm_generate_clarification(self, diagnosis: dict[str, Any], schema: ToolSchema) -> str:
        """Generate clarification using LLM."""
        if not self.llm_client:
            return self._rule_based_clarification(diagnosis, schema)

        prompt = f"""Given this tool schema and error analysis, generate a clear clarification
to add to the tool description that will prevent similar errors.

Tool Schema:
Name: {schema.name}
Description: {schema.description}
Arguments: {schema.arguments}
Required Fields: {schema.required_fields}

Error Analysis:
{diagnosis}

Generate a concise clarification (2-3 sentences) that explicitly states the constraints
that were violated. Format as a bulleted list of critical rules.
"""

        try:
            response = self.llm_client.generate(prompt)
            return response.strip()
        except Exception:
            return self._rule_based_clarification(diagnosis, schema)

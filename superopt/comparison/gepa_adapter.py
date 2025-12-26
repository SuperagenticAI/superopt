"""
GEPA Adapter for Agent Execution

Implements GEPAAdapter interface for executing coding agent tasks.
This adapter allows GEPA to optimize prompts by evaluating them
on agent execution tasks.

This adapter implements the GEPAAdapter Protocol from the gepa package
(install with: pip install gepa). It integrates with SuperOpt's agent
execution system to enable GEPA prompt optimization on coding tasks.
"""

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from superopt.adapters.base import AgentAdapter
from superopt.comparison.models import ModelConfig
from superopt.core.trace import ExecutionTrace


# Type definitions matching GEPA's expectations
# Using TypedDict for compatibility with GEPA's expected data format
class AgentDataInst(TypedDict, total=False):
    """Data instance for agent tasks."""

    input: str  # Task description (required)
    expected_output: str | None  # Optional expected output for evaluation
    metadata: dict[str, Any] | None  # Optional metadata


class AgentTrajectory(TypedDict, total=False):
    """Trajectory from agent execution."""

    data: AgentDataInst  # Task data instance
    trace: ExecutionTrace | None  # Execution trace (optional for serialization)
    full_response: str  # Agent's full response/output (required)


class AgentRolloutOutput(TypedDict, total=False):
    """Output from agent execution."""

    success: bool  # Whether task succeeded
    trace: ExecutionTrace | None  # Execution trace (optional for serialization)
    response: str  # Agent response text (required)


# Note: TypedDict doesn't support spaces in keys, so we use a regular dict type
# The actual dict will use "Generated Outputs" as the key to match GEPA's format
AgentReflectiveRecord = dict[str, Any]


class AgentGEPAAdapter:
    """
    GEPA adapter for agent execution.

    Implements GEPAAdapter interface to allow GEPA to optimize
    agent prompts by evaluating them on coding tasks.
    """

    def __init__(
        self,
        agent_adapter: AgentAdapter,
        model_config: ModelConfig | None = None,
        failure_score: float = 0.0,
    ):
        """
        Initialize agent GEPA adapter.

        Args:
            agent_adapter: Agent adapter for executing tasks
            model_config: Model configuration (optional)
            failure_score: Score to assign to failed tasks (default: 0.0)
        """
        self.agent_adapter = agent_adapter
        self.model_config = model_config
        self.failure_score = failure_score

    def _extract_response_from_trace(self, trace: ExecutionTrace) -> str:
        """
        Extract response text from execution trace.

        Args:
            trace: Execution trace

        Returns:
            Response string extracted from trace
        """
        # Use last model output if available
        if trace.model_outputs:
            return trace.model_outputs[-1]

        # Fallback: construct response from execution results
        if trace.execution_results:
            result_str = str(trace.execution_results)
            if len(result_str) > 500:
                return result_str[:500] + "..."
            return result_str

        # Fallback: use summary if available
        if trace.success:
            return f"Task completed successfully: {trace.task_description}"
        elif trace.failure_message:
            return f"Task failed: {trace.failure_message}"
        else:
            return (
                f"Task execution completed with status: {'success' if trace.success else 'failure'}"
            )

    def _calculate_score(self, trace: ExecutionTrace) -> float:
        """
        Calculate nuanced score for a task execution trace.

        Enhanced scoring considers:
        - Base success/failure (1.0 for success, scaled for failures)
        - Partial success indicators (some progress made)
        - Token efficiency (penalize excessive usage)
        - Error severity (different failure types)
        - Progress indicators (tool calls, retrieval attempts)

        Args:
            trace: Execution trace to score

        Returns:
            Score between failure_score and 1.0 (higher is better)
        """
        # Base score: success gets 1.0
        if trace.success:
            base_score = 1.0

            # Apply token efficiency penalty for successful runs
            # Normalize: assume reasonable task uses ~1000-5000 tokens
            # Penalize if significantly more
            if trace.token_count:
                if trace.token_count > 10000:
                    # Heavy penalty for very high token usage
                    efficiency_penalty = 0.1 * min((trace.token_count - 10000) / 10000, 1.0)
                    base_score = max(0.5, base_score - efficiency_penalty)
                elif trace.token_count > 5000:
                    # Moderate penalty
                    efficiency_penalty = 0.05 * (trace.token_count - 5000) / 5000
                    base_score = max(0.7, base_score - efficiency_penalty)

            return base_score

        # Failure case: start with failure_score and add partial credit
        score = self.failure_score

        # Partial success indicators
        partial_credit = 0.0

        # 1. Tool calls made (shows agent attempted the task)
        successful_tool_calls = len(trace.tool_calls) - len(trace.tool_errors)
        if successful_tool_calls > 0:
            # Credit for making progress
            partial_credit += 0.2 * min(successful_tool_calls / 5.0, 1.0)

        # 2. Retrieval attempts (shows agent tried to find context)
        if trace.retrieval_queries:
            successful_retrievals = sum(
                1 for q in trace.retrieval_queries if len(q.retrieved_documents) > 0
            )
            if successful_retrievals > 0:
                partial_credit += 0.1 * min(successful_retrievals / 3.0, 1.0)

        # 3. Model outputs generated (shows agent produced something)
        if trace.model_outputs:
            partial_credit += 0.1 * min(len(trace.model_outputs) / 3.0, 1.0)

        # 4. Error severity adjustment
        error_severity_multiplier = 1.0

        if trace.failure_type:
            # Different failure types indicate different levels of prompt issues
            if trace.failure_type.value == "PROMPT":
                # Prompt failures are most relevant for GEPA optimization
                error_severity_multiplier = 0.9  # Slight penalty
            elif trace.failure_type.value == "TOOL":
                # Tool errors might be fixable with better instructions
                error_severity_multiplier = 0.7  # Moderate penalty
            elif trace.failure_type.value == "RETRIEVAL":
                # Retrieval failures less related to prompt
                error_severity_multiplier = 0.8  # Moderate penalty
            elif trace.failure_type.value == "MEMORY":
                # Memory issues less related to prompt
                error_severity_multiplier = 0.85  # Slight penalty

        # 5. Compiler errors vs runtime errors
        # Compiler errors often indicate prompt issues (wrong code structure)
        # Runtime errors might be environmental
        if trace.compiler_errors:
            # Compiler errors suggest prompt could be improved
            error_severity_multiplier *= 0.9
        elif trace.runtime_exceptions:
            # Runtime exceptions less related to prompt
            error_severity_multiplier *= 0.95

        # Calculate final score
        # Start with failure_score, add partial credit, apply severity multiplier
        score = self.failure_score + partial_credit
        score = score * error_severity_multiplier

        # Ensure score is within bounds [failure_score, 0.9]
        # (0.9 max for failures to distinguish from success)
        score = max(self.failure_score, min(0.9, score))

        return score

    def evaluate(
        self,
        batch: list[AgentDataInst],
        candidate: dict[str, str],
        capture_traces: bool = False,
    ):
        """
        Evaluate candidate prompt on batch of tasks.

        Implements GEPAAdapter.evaluate() protocol.

        Args:
            batch: List of task data instances (AgentDataInst)
            candidate: Dictionary with prompt components (e.g., {"system_prompt": "..."})
            capture_traces: Whether to capture execution traces for reflection

        Returns:
            EvaluationBatch with outputs, scores, and optionally trajectories

        Note:
            - Never raises exceptions for individual example failures
            - Returns valid EvaluationBatch even on errors
            - Scores: higher is better (1.0 for success, failure_score for failure)
        """
        # Import here to avoid dependency if gepa not installed
        try:
            from gepa.core.adapter import EvaluationBatch
        except ImportError:
            raise ImportError("GEPA is not installed. Install with: pip install gepa")

        outputs: list[AgentRolloutOutput] = []
        scores: list[float] = []
        trajectories: list[AgentTrajectory] | None = [] if capture_traces else None

        # Extract system prompt from candidate (GEPA uses component name -> text mapping)
        # Default to first component or "system_prompt" key
        system_prompt = candidate.get("system_prompt", "")
        if not system_prompt and candidate:
            # If no "system_prompt" key, use first component value
            system_prompt = next(iter(candidate.values()), "")

        # Create environment with candidate prompt
        from superopt.core.environment import AgenticEnvironment, PromptConfig

        environment = AgenticEnvironment(
            prompts=PromptConfig(system_prompt=system_prompt),
        )

        # Execute each task in batch
        for data_inst in batch:
            try:
                # Extract task description from data instance
                # Handle both dict and TypedDict access patterns
                if isinstance(data_inst, dict):
                    task_description = data_inst.get("input", "")
                else:
                    task_description = getattr(data_inst, "input", "")

                if not task_description:
                    # Skip empty tasks
                    outputs.append(
                        {
                            "success": False,
                            "response": "Empty task description",
                        }
                    )
                    scores.append(self.failure_score)
                    if trajectories is not None:
                        trajectories.append(
                            {
                                "data": data_inst,
                                "full_response": "Empty task description",
                            }
                        )
                    continue

                # Execute task with candidate prompt
                trace = self.agent_adapter.execute(
                    task_description=task_description,
                    environment=environment,
                )

                # Determine success
                success = trace.success

                # Calculate nuanced score using enhanced scoring logic
                score = self._calculate_score(trace)

                # Extract response from trace
                response = self._extract_response_from_trace(trace)

                # Create output (TypedDict-compatible dict)
                output: AgentRolloutOutput = {
                    "success": success,
                    "response": response,
                    # Note: trace is not included in output for serialization compatibility
                    # Trajectory will contain trace if needed
                }

                outputs.append(output)
                scores.append(score)

                # Capture trajectory if requested (for make_reflective_dataset)
                if trajectories is not None:
                    # Ensure data_inst is properly formatted
                    traj_data: AgentDataInst = {}
                    if isinstance(data_inst, dict):
                        traj_data = {
                            "input": data_inst.get("input", task_description),
                            "expected_output": data_inst.get("expected_output"),
                            "metadata": data_inst.get("metadata"),
                        }
                    else:
                        traj_data = {
                            "input": getattr(data_inst, "input", task_description),
                            "expected_output": getattr(data_inst, "expected_output", None),
                            "metadata": getattr(data_inst, "metadata", None),
                        }

                    trajectory: AgentTrajectory = {
                        "data": traj_data,
                        "full_response": response,
                        "trace": trace,  # Store trace for detailed analysis in make_reflective_dataset
                    }
                    trajectories.append(trajectory)

            except Exception as e:
                # Handle exceptions gracefully - never raise for individual failures
                # Return failure score but don't crash (per GEPA contract)
                task_desc = ""
                if isinstance(data_inst, dict):
                    task_desc = data_inst.get("input", "")
                else:
                    task_desc = getattr(data_inst, "input", "")

                error_response = f"Error executing task: {str(e)}"

                outputs.append(
                    {
                        "success": False,
                        "response": error_response,
                    }
                )
                scores.append(self.failure_score)

                if trajectories is not None:
                    traj_data: AgentDataInst = {
                        "input": task_desc or "Unknown task",
                    }
                    trajectories.append(
                        {
                            "data": traj_data,
                            "full_response": error_response,
                        }
                    )

        # Ensure correct lengths (GEPA contract requirement)
        assert len(outputs) == len(scores) == len(batch), (
            f"Length mismatch: outputs={len(outputs)}, scores={len(scores)}, batch={len(batch)}"
        )

        if capture_traces:
            assert trajectories is not None and len(trajectories) == len(batch), (
                f"Trajectories length mismatch: {len(trajectories) if trajectories else 0} != {len(batch)}"
            )

        return EvaluationBatch(
            outputs=outputs,
            scores=scores,
            trajectories=trajectories,
        )

    def _extract_detailed_failure_analysis(
        self, trace: ExecutionTrace | None, task_input: str, full_response: str
    ) -> str:
        """
        Extract detailed failure analysis from execution trace.

        Args:
            trace: Execution trace (may be None)
            task_input: Task input description
            full_response: Agent's full response

        Returns:
            Detailed failure analysis string
        """
        if not trace:
            # Fallback to basic analysis if trace not available
            return f"Task execution failed. Agent response: '{full_response[:200]}...'"

        failure_parts = []

        # 1. Failure type and message
        if trace.failure_type:
            failure_parts.append(f"Failure type: {trace.failure_type.value}")
        if trace.failure_message:
            failure_parts.append(f"Error: {trace.failure_message}")

        # 2. Tool call analysis
        if trace.tool_calls or trace.tool_errors:
            successful_calls = len(trace.tool_calls) - len(trace.tool_errors)
            total_calls = len(trace.tool_calls)

            if trace.tool_errors:
                # Extract specific tool errors
                error_summaries = []
                for error in trace.tool_errors[:3]:  # Limit to first 3 errors
                    error_msg = error.error_message or "Unknown error"
                    error_summaries.append(f"{error.tool_name}: {error_msg[:100]}")

                failure_parts.append(
                    f"Tool errors ({len(trace.tool_errors)}/{total_calls} failed): "
                    f"{'; '.join(error_summaries)}"
                )
            elif successful_calls > 0:
                # Some tools succeeded
                tool_names = [call.tool_name for call in trace.tool_calls[:5]]
                failure_parts.append(
                    f"Tools called ({successful_calls} successful): {', '.join(tool_names)}"
                )

        # 3. Compiler/runtime errors
        if trace.compiler_errors:
            error_preview = trace.compiler_errors[0][:150] if trace.compiler_errors else "Unknown"
            failure_parts.append(
                f"Compiler errors ({len(trace.compiler_errors)}): {error_preview}..."
            )

        if trace.runtime_exceptions:
            exception_preview = (
                trace.runtime_exceptions[0][:150] if trace.runtime_exceptions else "Unknown"
            )
            failure_parts.append(
                f"Runtime exceptions ({len(trace.runtime_exceptions)}): {exception_preview}..."
            )

        # 4. Retrieval analysis
        if trace.retrieval_queries:
            empty_queries = sum(
                1 for q in trace.retrieval_queries if len(q.retrieved_documents) == 0
            )
            successful_queries = len(trace.retrieval_queries) - empty_queries

            if empty_queries > 0:
                query_texts = [
                    q.query[:50]
                    for q in trace.retrieval_queries[:3]
                    if len(q.retrieved_documents) == 0
                ]
                failure_parts.append(
                    f"Retrieval failures ({empty_queries}/{len(trace.retrieval_queries)} empty): "
                    f"Queries like '{'; '.join(query_texts)}...' returned no results"
                )
            elif successful_queries > 0:
                failure_parts.append(
                    f"Retrieval succeeded ({successful_queries} queries with results)"
                )

        # 5. Token usage (for efficiency feedback)
        if trace.token_count:
            if trace.token_count > 10000:
                failure_parts.append(
                    f"High token usage ({trace.token_count} tokens) - consider more efficient approach"
                )

        # 6. Actionable suggestions based on failure patterns
        suggestions = []

        if trace.tool_errors and trace.invalid_arguments():
            suggestions.append("Consider adding clearer instructions for tool argument formats")

        if trace.missing_symbol():
            suggestions.append(
                "Consider improving retrieval instructions or adding context about required symbols"
            )

        if trace.retrieval_empty():
            suggestions.append(
                "Consider refining query generation or providing more context in the prompt"
            )

        if trace.compiler_errors:
            suggestions.append("Consider adding examples of correct code structure or syntax")

        if trace.output_format_error():
            suggestions.append("Consider clarifying the expected output format with examples")

        # Combine all information
        analysis_parts = []

        if failure_parts:
            analysis_parts.append("Failure details: " + " | ".join(failure_parts))

        if suggestions:
            analysis_parts.append("Suggestions for improvement: " + "; ".join(suggestions))

        if not analysis_parts:
            # Fallback if no detailed info available
            analysis_parts.append(f"Task execution failed. Response: '{full_response[:200]}...'")

        return " ".join(analysis_parts)

    def make_reflective_dataset(
        self,
        candidate: dict[str, str],
        eval_batch,
        components_to_update: list[str],
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        """
        Create reflective dataset from evaluation results.

        Implements GEPAAdapter.make_reflective_dataset() protocol.
        Extracts detailed failure information from traces to help GEPA
        reflect on prompt performance and propose improvements.

        Args:
            candidate: Current candidate prompt (same as evaluated in evaluate())
            eval_batch: EvaluationBatch from evaluate(..., capture_traces=True)
            components_to_update: List of component names to update

        Returns:
            Mapping from component name to list of reflective records.
            Each record is JSON-serializable and follows GEPA's recommended schema:
            {
                "Inputs": str,              # Task input
                "Generated Outputs": str,    # Agent's output
                "Feedback": str,            # Detailed performance feedback
                "Score": float              # Score for this example
            }
        """
        # Ensure trajectories are available (required for reflection)
        trajectories = eval_batch.trajectories
        if trajectories is None:
            raise ValueError(
                "Trajectories are required to build a reflective dataset. "
                "Call evaluate() with capture_traces=True."
            )

        reflective_dataset: dict[str, list[AgentReflectiveRecord]] = {}
        scores = eval_batch.scores
        outputs = eval_batch.outputs

        # For each component to update
        for component_name in components_to_update:
            records: list[AgentReflectiveRecord] = []

            # Build reflective records from trajectories, scores, and outputs
            trace_instances = list(zip(trajectories, scores, outputs, strict=False))

            for traj, score, _output in trace_instances:
                if traj is None:
                    continue

                # Extract data from trajectory (TypedDict access)
                if isinstance(traj, dict):
                    data_inst = traj.get("data", {})
                    full_response = traj.get("full_response", "")
                    trace = traj.get("trace")  # Get trace for detailed analysis
                else:
                    # Handle object-style access if needed
                    data_inst = getattr(traj, "data", {})
                    full_response = getattr(traj, "full_response", "")
                    trace = getattr(traj, "trace", None)

                # Extract input from data_inst
                if isinstance(data_inst, dict):
                    task_input = data_inst.get("input", "")
                else:
                    task_input = getattr(data_inst, "input", "")

                # Build detailed feedback based on success/failure
                if score >= 0.9:  # Success (or near-success)
                    # Success case - provide positive feedback with efficiency notes
                    feedback_parts = [
                        "The task was completed successfully.",
                        f"Task: '{task_input[:150]}...'",
                    ]

                    if trace and trace.token_count and trace.token_count > 5000:
                        feedback_parts.append(
                            f"Note: Token usage was high ({trace.token_count} tokens) - "
                            "consider optimizing for efficiency."
                        )

                    feedback = " ".join(feedback_parts)
                else:
                    # Failure case - extract detailed failure patterns
                    feedback = self._extract_detailed_failure_analysis(
                        trace=trace, task_input=task_input, full_response=full_response
                    )

                    # Add context about what was attempted
                    if trace:
                        if trace.tool_calls:
                            attempted_actions = [call.tool_name for call in trace.tool_calls[:3]]
                            feedback += f" | Attempted actions: {', '.join(attempted_actions)}"

                        if trace.model_outputs:
                            feedback += f" | Generated {len(trace.model_outputs)} model outputs"

                # Create reflective record following GEPA's recommended schema
                # Note: Using string keys to match GEPA's expected format
                record = {
                    "Inputs": task_input,
                    "Generated Outputs": full_response[:500],  # Limit length for readability
                    "Feedback": feedback,
                    "Score": score,
                }

                records.append(record)

            # Ensure we have at least one record per component
            if len(records) == 0:
                raise ValueError(
                    f"No valid predictions found for component '{component_name}'. "
                    "Cannot build reflective dataset."
                )

            reflective_dataset[component_name] = records

        return reflective_dataset

    def propose_new_texts(
        self,
        candidate: dict[str, str],
        reflective_dataset: Mapping[str, Sequence[Mapping[str, Any]]],
        components_to_update: list[str],
    ) -> dict[str, str]:
        """
        Optional: Custom proposal logic.

        If not implemented, GEPA will use its default reflective mutation.
        This allows custom proposal strategies if needed.

        Args:
            candidate: Current candidate
            reflective_dataset: Reflective dataset from make_reflective_dataset
            components_to_update: Components to update

        Returns:
            New candidate with updated components
        """
        # Use GEPA's default proposal logic
        # Can be overridden for custom strategies
        return candidate

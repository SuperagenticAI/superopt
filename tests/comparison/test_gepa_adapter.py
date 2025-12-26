"""
Unit tests for GEPA Adapter.

Tests the AgentGEPAAdapter implementation including:
- evaluate() method with various scenarios
- make_reflective_dataset() method
- Scoring logic (_calculate_score)
- Response extraction (_extract_response_from_trace)
- Failure analysis (_extract_detailed_failure_analysis)
"""

from typing import Any
from unittest.mock import Mock

import pytest

from superopt.adapters.base import AgentAdapter
from superopt.comparison.gepa_adapter import (
    AgentDataInst,
    AgentGEPAAdapter,
)
from superopt.comparison.models import ModelConfig, ModelProvider
from superopt.core.environment import AgenticEnvironment, PromptConfig
from superopt.core.trace import (
    ExecutionTrace,
    FailureType,
    RetrievalQuery,
    ToolCall,
)


class MockAgentAdapter(AgentAdapter):
    """Mock agent adapter for testing."""

    def __init__(self, trace_to_return: ExecutionTrace):
        self.trace_to_return = trace_to_return
        self.last_task = None
        self.last_environment = None

    def execute(self, task_description: str, environment: AgenticEnvironment) -> ExecutionTrace:
        self.last_task = task_description
        self.last_environment = environment
        return self.trace_to_return

    def extract_environment(self) -> AgenticEnvironment:
        return AgenticEnvironment(prompts=PromptConfig(system_prompt="Default system prompt"))

    def apply_environment(self, environment: AgenticEnvironment):
        pass

    def get_agent_info(self) -> dict[str, Any]:
        return {"name": "mock_agent"}


def create_success_trace(task_description: str = "Test task") -> ExecutionTrace:
    """Create a successful execution trace."""
    return ExecutionTrace(
        task_description=task_description,
        success=True,
        token_count=2000,
        tool_calls=[
            ToolCall(tool_name="read_file", arguments={"path": "test.py"}, success=True),
            ToolCall(
                tool_name="write_file",
                arguments={"path": "test.py", "content": "code"},
                success=True,
            ),
        ],
        model_outputs=["Generated code successfully"],
    )


def create_failure_trace(
    task_description: str = "Test task",
    failure_type: FailureType = FailureType.PROMPT,
    tool_errors: list[ToolCall] = None,
    compiler_errors: list[str] = None,
) -> ExecutionTrace:
    """Create a failed execution trace."""
    return ExecutionTrace(
        task_description=task_description,
        success=False,
        failure_type=failure_type,
        failure_message="Task failed",
        token_count=1500,
        tool_calls=[
            ToolCall(tool_name="read_file", arguments={"path": "test.py"}, success=True),
        ],
        tool_errors=tool_errors or [],
        compiler_errors=compiler_errors or [],
        model_outputs=["Attempted to generate code"],
    )


class TestAgentGEPAAdapter:
    """Test suite for AgentGEPAAdapter."""

    def test_init(self):
        """Test adapter initialization."""
        agent_adapter = Mock(MockAgentAdapter)
        adapter = AgentGEPAAdapter(
            agent_adapter=agent_adapter,
            failure_score=0.0,
        )

        assert adapter.agent_adapter == agent_adapter
        assert adapter.failure_score == 0.0
        assert adapter.model_config is None

    def test_init_with_model_config(self):
        """Test adapter initialization with model config."""
        agent_adapter = Mock(MockAgentAdapter)
        model_config = ModelConfig(
            task_model="test-model",
            reflection_model="test-reflection",
            provider=ModelProvider.OLLAMA,
        )
        adapter = AgentGEPAAdapter(
            agent_adapter=agent_adapter,
            model_config=model_config,
            failure_score=0.1,
        )

        assert adapter.model_config == model_config
        assert adapter.failure_score == 0.1

    def test_extract_response_from_trace_with_model_outputs(self):
        """Test response extraction when model outputs exist."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = ExecutionTrace(
            task_description="test",
            model_outputs=["output1", "output2", "final_output"],
        )

        response = adapter._extract_response_from_trace(trace)
        assert response == "final_output"

    def test_extract_response_from_trace_with_execution_results(self):
        """Test response extraction from execution results."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = ExecutionTrace(
            task_description="test",
            execution_results={"result": "success", "data": "test_data"},
        )

        response = adapter._extract_response_from_trace(trace)
        assert "success" in response
        assert "test_data" in response

    def test_extract_response_from_trace_success_fallback(self):
        """Test response extraction fallback for success."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = ExecutionTrace(
            task_description="test task",
            success=True,
        )

        response = adapter._extract_response_from_trace(trace)
        assert "completed successfully" in response
        assert "test task" in response

    def test_extract_response_from_trace_failure_fallback(self):
        """Test response extraction fallback for failure."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = ExecutionTrace(
            task_description="test task",
            success=False,
            failure_message="Error occurred",
        )

        response = adapter._extract_response_from_trace(trace)
        assert "failed" in response
        assert "Error occurred" in response

    def test_calculate_score_success(self):
        """Test scoring for successful execution."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_success_trace()

        score = adapter._calculate_score(trace)
        assert score == 1.0

    def test_calculate_score_success_high_tokens(self):
        """Test scoring for successful execution with high token usage."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_success_trace()
        trace.token_count = 12000  # High token usage

        score = adapter._calculate_score(trace)
        assert 0.5 <= score < 1.0  # Should be penalized

    def test_calculate_score_failure_basic(self):
        """Test scoring for basic failure."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace()

        score = adapter._calculate_score(trace)
        assert adapter.failure_score <= score < 0.9

    def test_calculate_score_failure_with_tool_calls(self):
        """Test scoring for failure with successful tool calls (partial credit)."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace()
        trace.tool_calls = [
            ToolCall(tool_name="tool1", arguments={}, success=True),
            ToolCall(tool_name="tool2", arguments={}, success=True),
            ToolCall(tool_name="tool3", arguments={}, success=True),
        ]

        score = adapter._calculate_score(trace)
        # Should have partial credit for tool calls
        assert score > adapter.failure_score

    def test_calculate_score_failure_with_retrieval(self):
        """Test scoring for failure with successful retrievals."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace()
        trace.retrieval_queries = [
            RetrievalQuery(query="test", retrieved_documents=[{"doc": "1"}]),
            RetrievalQuery(query="test2", retrieved_documents=[{"doc": "2"}]),
        ]

        score = adapter._calculate_score(trace)
        # Should have partial credit for retrievals
        assert score > adapter.failure_score

    def test_calculate_score_failure_prompt_type(self):
        """Test scoring for prompt-related failures."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace(failure_type=FailureType.PROMPT)

        score = adapter._calculate_score(trace)
        # Prompt failures are most relevant for GEPA
        assert adapter.failure_score <= score < 0.9

    def test_calculate_score_failure_tool_type(self):
        """Test scoring for tool-related failures."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace(failure_type=FailureType.TOOL)

        score = adapter._calculate_score(trace)
        # Tool errors get moderate penalty
        assert adapter.failure_score <= score < 0.9

    def test_calculate_score_failure_with_compiler_errors(self):
        """Test scoring for failures with compiler errors."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace(compiler_errors=["SyntaxError: invalid syntax"])

        score = adapter._calculate_score(trace)
        # Compiler errors suggest prompt issues
        assert adapter.failure_score <= score < 0.9

    def test_evaluate_success(self):
        """Test evaluate() with successful execution."""
        trace = create_success_trace()
        agent_adapter = MockAgentAdapter(trace)
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [
            AgentDataInst(input="Task 1"),
            AgentDataInst(input="Task 2"),
        ]
        candidate = {"system_prompt": "Test prompt"}

        result = adapter.evaluate(batch, candidate, capture_traces=False)

        assert len(result.outputs) == 2
        assert len(result.scores) == 2
        assert result.trajectories is None
        assert all(output["success"] for output in result.outputs)
        assert all(score == 1.0 for score in result.scores)

    def test_evaluate_with_traces(self):
        """Test evaluate() with trace capture enabled."""
        trace = create_success_trace()
        agent_adapter = MockAgentAdapter(trace)
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [AgentDataInst(input="Task 1")]
        candidate = {"system_prompt": "Test prompt"}

        result = adapter.evaluate(batch, candidate, capture_traces=True)

        assert result.trajectories is not None
        assert len(result.trajectories) == 1
        assert result.trajectories[0]["data"]["input"] == "Task 1"

    def test_evaluate_failure(self):
        """Test evaluate() with failed execution."""
        trace = create_failure_trace()
        agent_adapter = MockAgentAdapter(trace)
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [AgentDataInst(input="Task 1")]
        candidate = {"system_prompt": "Test prompt"}

        result = adapter.evaluate(batch, candidate, capture_traces=False)

        assert len(result.outputs) == 1
        assert not result.outputs[0]["success"]
        assert result.scores[0] < 1.0

    def test_evaluate_empty_task(self):
        """Test evaluate() with empty task description."""
        trace = create_success_trace()
        agent_adapter = MockAgentAdapter(trace)
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [AgentDataInst(input="")]
        candidate = {"system_prompt": "Test prompt"}

        result = adapter.evaluate(batch, candidate, capture_traces=False)

        assert len(result.outputs) == 1
        assert not result.outputs[0]["success"]
        assert result.scores[0] == adapter.failure_score

    def test_evaluate_exception_handling(self):
        """Test evaluate() handles exceptions gracefully."""
        agent_adapter = Mock()
        agent_adapter.execute = Mock(side_effect=Exception("Test error"))
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [AgentDataInst(input="Task 1")]
        candidate = {"system_prompt": "Test prompt"}

        result = adapter.evaluate(batch, candidate, capture_traces=False)

        # Should not raise, but return failure
        assert len(result.outputs) == 1
        assert not result.outputs[0]["success"]
        assert "Error" in result.outputs[0]["response"]

    def test_evaluate_candidate_extraction(self):
        """Test evaluate() extracts prompt from candidate correctly."""
        trace = create_success_trace()
        agent_adapter = MockAgentAdapter(trace)
        adapter = AgentGEPAAdapter(agent_adapter, failure_score=0.0)

        batch = [AgentDataInst(input="Task 1")]

        # Test with "system_prompt" key
        candidate1 = {"system_prompt": "Prompt 1"}
        adapter.evaluate(batch, candidate1, capture_traces=False)
        assert agent_adapter.last_environment.prompts.system_prompt == "Prompt 1"

        # Test with first component value
        candidate2 = {"instruction": "Prompt 2"}
        adapter.evaluate(batch, candidate2, capture_traces=False)
        assert agent_adapter.last_environment.prompts.system_prompt == "Prompt 2"

    def test_extract_detailed_failure_analysis_no_trace(self):
        """Test failure analysis when trace is None."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        analysis = adapter._extract_detailed_failure_analysis(
            trace=None, task_input="test task", full_response="error response"
        )

        assert "failed" in analysis.lower()
        assert "error response" in analysis

    def test_extract_detailed_failure_analysis_with_tool_errors(self):
        """Test failure analysis with tool errors."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace()
        trace.tool_errors = [
            ToolCall(
                tool_name="edit_file",
                arguments={"path": "test.py"},
                success=False,
                error_message="Invalid line number",
            )
        ]

        analysis = adapter._extract_detailed_failure_analysis(
            trace=trace, task_input="test task", full_response="error"
        )

        assert "tool error" in analysis.lower() or "edit_file" in analysis.lower()
        assert "Invalid line number" in analysis

    def test_extract_detailed_failure_analysis_with_compiler_errors(self):
        """Test failure analysis with compiler errors."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace(compiler_errors=["SyntaxError: invalid syntax at line 5"])

        analysis = adapter._extract_detailed_failure_analysis(
            trace=trace, task_input="test task", full_response="error"
        )

        assert "compiler error" in analysis.lower()
        assert "SyntaxError" in analysis

    def test_extract_detailed_failure_analysis_with_retrieval_failures(self):
        """Test failure analysis with retrieval failures."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)
        trace = create_failure_trace()
        trace.retrieval_queries = [
            RetrievalQuery(query="test query", retrieved_documents=[]),
        ]

        analysis = adapter._extract_detailed_failure_analysis(
            trace=trace, task_input="test task", full_response="error"
        )

        assert "retrieval" in analysis.lower()
        assert "empty" in analysis.lower() or "no results" in analysis.lower()

    def test_make_reflective_dataset_success(self):
        """Test make_reflective_dataset() with successful examples."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        # Create mock eval_batch
        eval_batch = Mock()
        eval_batch.trajectories = [
            {
                "data": {"input": "Task 1"},
                "full_response": "Success response",
                "trace": create_success_trace("Task 1"),
            }
        ]
        eval_batch.scores = [1.0]
        eval_batch.outputs = [{"success": True, "response": "Success response"}]

        result = adapter.make_reflective_dataset(
            candidate={"system_prompt": "test"},
            eval_batch=eval_batch,
            components_to_update=["system_prompt"],
        )

        assert "system_prompt" in result
        assert len(result["system_prompt"]) == 1
        record = result["system_prompt"][0]
        assert record["Inputs"] == "Task 1"
        assert record["Score"] == 1.0
        assert "successfully" in record["Feedback"].lower()

    def test_make_reflective_dataset_failure(self):
        """Test make_reflective_dataset() with failed examples."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        trace = create_failure_trace("Task 1", compiler_errors=["SyntaxError"])

        eval_batch = Mock()
        eval_batch.trajectories = [
            {
                "data": {"input": "Task 1"},
                "full_response": "Error response",
                "trace": trace,
            }
        ]
        eval_batch.scores = [0.0]
        eval_batch.outputs = [{"success": False, "response": "Error response"}]

        result = adapter.make_reflective_dataset(
            candidate={"system_prompt": "test"},
            eval_batch=eval_batch,
            components_to_update=["system_prompt"],
        )

        assert "system_prompt" in result
        record = result["system_prompt"][0]
        assert record["Score"] == 0.0
        assert "failed" in record["Feedback"].lower() or "error" in record["Feedback"].lower()

    def test_make_reflective_dataset_no_trajectories(self):
        """Test make_reflective_dataset() raises error when trajectories missing."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        eval_batch = Mock()
        eval_batch.trajectories = None

        with pytest.raises(ValueError, match="Trajectories are required"):
            adapter.make_reflective_dataset(
                candidate={"system_prompt": "test"},
                eval_batch=eval_batch,
                components_to_update=["system_prompt"],
            )

    def test_make_reflective_dataset_empty_records(self):
        """Test make_reflective_dataset() raises error when no valid records."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        eval_batch = Mock()
        eval_batch.trajectories = []
        eval_batch.scores = []
        eval_batch.outputs = []

        with pytest.raises(ValueError, match="No valid predictions"):
            adapter.make_reflective_dataset(
                candidate={"system_prompt": "test"},
                eval_batch=eval_batch,
                components_to_update=["system_prompt"],
            )

    def test_propose_new_texts_default(self):
        """Test propose_new_texts() returns candidate unchanged (uses GEPA default)."""
        adapter = AgentGEPAAdapter(Mock(), failure_score=0.0)

        candidate = {"system_prompt": "test prompt"}
        reflective_dataset = {"system_prompt": []}

        result = adapter.propose_new_texts(
            candidate=candidate,
            reflective_dataset=reflective_dataset,
            components_to_update=["system_prompt"],
        )

        # Should return candidate unchanged (GEPA uses its default proposer)
        assert result == candidate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

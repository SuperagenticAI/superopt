"""
Data Processor for ACE Integration

Converts SuperOpt agent tasks to ACE format for context accumulation.
"""

from typing import Any


class AgentDataProcessor:
    """
    Data processor for agent tasks in ACE format.

    Converts SuperOpt task descriptions to ACE's expected format
    for playbook accumulation.
    """

    def __init__(self, task_name: str = "agent_tasks"):
        """
        Initialize the data processor.

        Args:
            task_name: Name of the task (for ACE logging)
        """
        self.task_name = task_name

    def process_task_data(self, raw_data: list[dict]) -> list[dict]:
        """
        Process task data for ACE.

        Args:
            raw_data: List of task dictionaries with 'input' and optionally 'output'

        Returns:
            Processed data in ACE format
        """
        processed_data = []

        for item in raw_data:
            # Extract input (task description)
            task_input = item.get("input", "")
            if isinstance(item, str):
                task_input = item

            # Extract expected output if available
            expected_output = item.get("output", "") if isinstance(item, dict) else ""

            # Create ACE format: context is the task, answer is expected output
            processed_item = {
                "context": task_input,
                "answer": expected_output,
                "all_context": f"Task: {task_input}\nAnswer: {expected_output}"
                if expected_output
                else f"Task: {task_input}",
            }

            processed_data.append(processed_item)

        return processed_data

    def format_for_generator(self, sample: dict[str, Any], playbook: str) -> str:
        """
        Format a sample with playbook for the generator.

        Args:
            sample: Sample dictionary with 'context' and 'answer'
            playbook: Current playbook content

        Returns:
            Formatted prompt for generator
        """
        context = sample.get("context", sample.get("all_context", ""))

        prompt = f"""You are an expert agent solving coding tasks. Use the following playbook to guide your approach:

{playbook}

---

Task: {context}

Provide a detailed solution approach and implementation."""

        return prompt

    def extract_answer(self, response: str) -> str:
        """
        Extract answer from generator response.

        Args:
            response: Generator's response text

        Returns:
            Extracted answer
        """
        # For agent tasks, the full response is the answer
        # This can be customized based on task format
        return response.strip()

    def evaluate_answer(self, generated: str, expected: str) -> bool:
        """
        Evaluate if generated answer matches expected.

        Args:
            generated: Generated answer
            expected: Expected answer

        Returns:
            True if answer is correct
        """
        # For agent tasks without ground truth, we can't evaluate directly
        # ACE will use execution feedback instead
        if not expected:
            return None  # No ground truth available

        # Simple string matching (can be enhanced)
        generated_lower = generated.lower().strip()
        expected_lower = expected.lower().strip()

        return expected_lower in generated_lower or generated_lower in expected_lower

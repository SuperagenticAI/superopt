"""
Base Adapter Interface for Agent Integration

Adapters allow SuperOpt to work with different agent frameworks by
providing a standardized interface for:
- Executing agents with environment configurations
- Capturing execution traces
- Extracting environment components
"""

from abc import ABC, abstractmethod
from typing import Any

from superopt.core.environment import AgenticEnvironment
from superopt.core.trace import ExecutionTrace


class AgentAdapter(ABC):
    """
    Base adapter interface for integrating agents with SuperOpt.

    Subclasses should implement methods to:
    1. Execute agents with given environment
    2. Capture execution traces
    3. Extract/apply environment configurations
    """

    @abstractmethod
    def execute(
        self,
        task_description: str,
        environment: AgenticEnvironment,
    ) -> ExecutionTrace:
        """
        Execute agent with given environment and capture trace.

        Args:
            task_description: Description of the task to execute
            environment: Agentic environment configuration

        Returns:
            Execution trace capturing the agent's interaction
        """
        pass

    @abstractmethod
    def extract_environment(self) -> AgenticEnvironment:
        """
        Extract current environment configuration from agent.

        Returns:
            Current agentic environment
        """
        pass

    @abstractmethod
    def apply_environment(self, environment: AgenticEnvironment):
        """
        Apply environment configuration to agent.

        Args:
            environment: Environment configuration to apply
        """
        pass

    @abstractmethod
    def get_agent_info(self) -> dict[str, Any]:
        """
        Get information about the underlying agent.

        Returns:
            Dictionary with agent metadata
        """
        pass

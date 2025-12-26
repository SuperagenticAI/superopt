"""Core abstractions for SuperOpt framework."""

from superopt.core.environment import AgenticEnvironment
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace

__all__ = ["AgenticEnvironment", "ExecutionTrace", "NaturalLanguageGradient"]

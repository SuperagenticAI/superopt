"""
SuperOpt: Agentic Environment Optimization for Autonomous AI Agents

A unified framework for optimizing agent environments (prompts, tools, retrieval, memory)
without modifying model parameters.
"""

__version__ = "0.1.0"

from superopt.core.environment import AgenticEnvironment
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace, FailureType
from superopt.optimizer import SuperOpt
from superopt.supercontroller import SuperController
from superopt.supermem import SuperMem
from superopt.superprompt import SuperPrompt
from superopt.superrag import SuperRAG
from superopt.superreflexion import SuperReflexion

__all__ = [
    "AgenticEnvironment",
    "ExecutionTrace",
    "FailureType",
    "NaturalLanguageGradient",
    "SuperController",
    "SuperPrompt",
    "SuperReflexion",
    "SuperRAG",
    "SuperMem",
    "SuperOpt",
]

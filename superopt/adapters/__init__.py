"""Adapters for integrating SuperOpt with different agent frameworks."""

from superopt.adapters.aider_adapter import AiderAdapter
from superopt.adapters.base import AgentAdapter
from superopt.adapters.codex_adapter import CodexAdapter
from superopt.adapters.letta_adapter import LettaAdapter

__all__ = [
    "AgentAdapter",
    "AiderAdapter",
    "LettaAdapter",
    "CodexAdapter",
]

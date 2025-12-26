"""
Natural Language Gradients (NLG)

Natural Language Gradients are structured sets of environment updates
derived from execution traces. Unlike numeric gradients, NLGs operate
over symbolic structures and are applied through deterministic update rules.
"""

from dataclasses import dataclass
from typing import Any

from superopt.core.environment import MemoryEntry


@dataclass
class NaturalLanguageGradient:
    """
    Natural Language Gradient: ∇_NL(τ) = { δ_P, δ_T, δ_R, δ_M }

    Each component corresponds to a discrete, interpretable patch
    applied to one environment layer.
    """

    delta_p: dict[str, Any] | None = None  # Prompt updates
    delta_t: dict[str, Any] | None = None  # Tool schema updates
    delta_r: dict[str, Any] | None = None  # Retrieval configuration updates
    delta_m: list[MemoryEntry] | None = None  # Memory updates

    source_trace_id: str | None = None
    generation_timestamp: str | None = None
    confidence: float = 1.0

    def is_empty(self) -> bool:
        """Check if gradient has no updates."""
        return (
            self.delta_p is None
            and self.delta_t is None
            and self.delta_r is None
            and (self.delta_m is None or len(self.delta_m) == 0)
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NLG to dictionary."""
        return {
            "delta_p": self.delta_p,
            "delta_t": self.delta_t,
            "delta_r": self.delta_r,
            "delta_m": [entry.to_dict() for entry in self.delta_m] if self.delta_m else None,
            "source_trace_id": self.source_trace_id,
            "generation_timestamp": self.generation_timestamp,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NaturalLanguageGradient":
        """Deserialize NLG from dictionary."""
        from superopt.core.environment import MemoryEntry

        delta_m = None
        if data.get("delta_m"):
            delta_m = [MemoryEntry.from_dict(entry) for entry in data["delta_m"]]

        return cls(
            delta_p=data.get("delta_p"),
            delta_t=data.get("delta_t"),
            delta_r=data.get("delta_r"),
            delta_m=delta_m,
            source_trace_id=data.get("source_trace_id"),
            generation_timestamp=data.get("generation_timestamp"),
            confidence=data.get("confidence", 1.0),
        )

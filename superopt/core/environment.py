"""
Agentic Environment Definition

The agentic environment Φ_t is defined as:
Φ_t = { P_t, T_t, R_t, M_t }

where:
- P_t: System prompts, instruction policies, and few-shot exemplars
- T_t: Tool schemas, APIs, execution protocols, and interface constraints
- R_t: Retrieval pipelines, chunking strategies, query generation, ranking
- M_t: Persistent memory, heuristics, reflections, rules, constraints
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from superopt.core.nlg import NaturalLanguageGradient


@dataclass
class PromptConfig:
    """System prompts and instruction policies."""

    system_prompt: str = ""
    instruction_policy: str = ""
    few_shot_exemplars: list[str] = field(default_factory=list)
    output_format_spec: str = ""
    behavioral_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_prompt": self.system_prompt,
            "instruction_policy": self.instruction_policy,
            "few_shot_exemplars": self.few_shot_exemplars,
            "output_format_spec": self.output_format_spec,
            "behavioral_constraints": self.behavioral_constraints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptConfig":
        return cls(
            system_prompt=data.get("system_prompt", ""),
            instruction_policy=data.get("instruction_policy", ""),
            few_shot_exemplars=data.get("few_shot_exemplars", []),
            output_format_spec=data.get("output_format_spec", ""),
            behavioral_constraints=data.get("behavioral_constraints", []),
        )


@dataclass
class ToolSchema:
    """Tool schema definition with arguments, types, and constraints."""

    name: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)  # name -> type/constraint
    required_fields: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
            "required_fields": self.required_fields,
            "constraints": self.constraints,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolSchema":
        return cls(
            name=data["name"],
            description=data["description"],
            arguments=data.get("arguments", {}),
            required_fields=data.get("required_fields", []),
            constraints=data.get("constraints", []),
            examples=data.get("examples", []),
        )


@dataclass
class RetrievalConfig:
    """Retrieval pipeline configuration."""

    top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    rerank_threshold: float = 0.7
    mode: str = "semantic"  # "semantic" or "structural"
    query_rewrite_strategy: str = "default"
    file_type_filters: list[str] = field(default_factory=list)
    dependency_expansion_depth: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_k": self.top_k,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "rerank_threshold": self.rerank_threshold,
            "mode": self.mode,
            "query_rewrite_strategy": self.query_rewrite_strategy,
            "file_type_filters": self.file_type_filters,
            "dependency_expansion_depth": self.dependency_expansion_depth,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetrievalConfig":
        return cls(
            top_k=data.get("top_k", 5),
            chunk_size=data.get("chunk_size", 512),
            chunk_overlap=data.get("chunk_overlap", 50),
            rerank_threshold=data.get("rerank_threshold", 0.7),
            mode=data.get("mode", "semantic"),
            query_rewrite_strategy=data.get("query_rewrite_strategy", "default"),
            file_type_filters=data.get("file_type_filters", []),
            dependency_expansion_depth=data.get("dependency_expansion_depth", 1),
        )


@dataclass
class MemoryEntry:
    """Typed memory entry with confidence and timestamp."""

    entry_type: str  # STRATEGY, TOOL_RULE, RAG_HEURISTIC, PROMPT_CONSTRAINT, etc.
    content: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    helpful_count: int = 0
    harmful_count: int = 0

    def decay(self, lambda_decay: float, current_time: datetime) -> float:
        """Apply exponential decay to confidence."""
        delta_t = (current_time - self.timestamp).total_seconds() / 3600  # hours
        return self.confidence * (1.0 - lambda_decay) ** delta_t

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_type": self.entry_type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "helpful_count": self.helpful_count,
            "harmful_count": self.harmful_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        from datetime import datetime

        return cls(
            entry_type=data["entry_type"],
            content=data["content"],
            confidence=data.get("confidence", 1.0),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            helpful_count=data.get("helpful_count", 0),
            harmful_count=data.get("harmful_count", 0),
        )


@dataclass
class AgenticEnvironment:
    """
    The complete agentic environment Φ_t = { P_t, T_t, R_t, M_t }

    This is the mutable optimization target in SuperOpt.
    """

    prompts: PromptConfig = field(default_factory=PromptConfig)
    tools: dict[str, ToolSchema] = field(default_factory=dict)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    memory: list[MemoryEntry] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def apply_update(
        self, nlg: "NaturalLanguageGradient", alpha: float = 1.0
    ) -> "AgenticEnvironment":
        """
        Apply a Natural Language Gradient update to the environment.

        Args:
            nlg: The Natural Language Gradient containing updates
            alpha: Update acceptance rate (0.0 to 1.0)

        Returns:
            New environment with updates applied
        """
        new_env = AgenticEnvironment(
            prompts=self.prompts,
            tools=self.tools.copy(),
            retrieval=self.retrieval,
            memory=self.memory.copy(),
            timestamp=datetime.now(),
        )

        # Apply prompt updates
        if nlg.delta_p:
            new_env.prompts = self._apply_prompt_update(new_env.prompts, nlg.delta_p, alpha)

        # Apply tool updates
        if nlg.delta_t:
            new_env.tools = self._apply_tool_update(new_env.tools, nlg.delta_t, alpha)

        # Apply retrieval updates
        if nlg.delta_r:
            new_env.retrieval = self._apply_retrieval_update(new_env.retrieval, nlg.delta_r, alpha)

        # Apply memory updates
        if nlg.delta_m:
            new_env.memory = self._apply_memory_update(new_env.memory, nlg.delta_m, alpha)

        return new_env

    def _apply_prompt_update(
        self, prompts: PromptConfig, delta_p: dict[str, Any], alpha: float
    ) -> PromptConfig:
        """Apply prompt updates."""
        # Simple merge strategy - can be enhanced
        new_prompts = PromptConfig(
            system_prompt=prompts.system_prompt + "\n" + delta_p.get("additions", ""),
            instruction_policy=prompts.instruction_policy,
            few_shot_exemplars=prompts.few_shot_exemplars + delta_p.get("new_exemplars", []),
            output_format_spec=prompts.output_format_spec,
            behavioral_constraints=prompts.behavioral_constraints
            + delta_p.get("new_constraints", []),
        )
        return new_prompts

    def _apply_tool_update(
        self, tools: dict[str, ToolSchema], delta_t: dict[str, Any], alpha: float
    ) -> dict[str, ToolSchema]:
        """Apply tool schema updates."""
        new_tools = tools.copy()
        for tool_name, update in delta_t.items():
            if tool_name in new_tools:
                schema = new_tools[tool_name]
                # Append clarifications to description
                if "clarification" in update:
                    schema.description += "\n\n" + update["clarification"]
                # Add new constraints
                if "new_constraints" in update:
                    schema.constraints.extend(update["new_constraints"])
        return new_tools

    def _apply_retrieval_update(
        self, retrieval: RetrievalConfig, delta_r: dict[str, Any], alpha: float
    ) -> RetrievalConfig:
        """Apply retrieval configuration updates."""
        new_retrieval = RetrievalConfig(
            top_k=delta_r.get("top_k", retrieval.top_k),
            chunk_size=delta_r.get("chunk_size", retrieval.chunk_size),
            chunk_overlap=delta_r.get("chunk_overlap", retrieval.chunk_overlap),
            rerank_threshold=delta_r.get("rerank_threshold", retrieval.rerank_threshold),
            mode=delta_r.get("mode", retrieval.mode),
            query_rewrite_strategy=delta_r.get(
                "query_rewrite_strategy", retrieval.query_rewrite_strategy
            ),
            file_type_filters=delta_r.get("file_type_filters", retrieval.file_type_filters),
            dependency_expansion_depth=delta_r.get(
                "dependency_expansion_depth", retrieval.dependency_expansion_depth
            ),
        )
        return new_retrieval

    def _apply_memory_update(
        self, memory: list[MemoryEntry], delta_m: list[MemoryEntry], alpha: float
    ) -> list[MemoryEntry]:
        """Apply memory updates."""
        new_memory = memory.copy()
        new_memory.extend(delta_m)
        return new_memory

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompts": self.prompts.to_dict(),
            "tools": {name: schema.to_dict() for name, schema in self.tools.items()},
            "retrieval": self.retrieval.to_dict(),
            "memory": [entry.to_dict() for entry in self.memory],
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgenticEnvironment":
        from datetime import datetime

        return cls(
            prompts=PromptConfig.from_dict(data.get("prompts", {})),
            tools={
                name: ToolSchema.from_dict(schema) for name, schema in data.get("tools", {}).items()
            },
            retrieval=RetrievalConfig.from_dict(data.get("retrieval", {})),
            memory=[MemoryEntry.from_dict(entry) for entry in data.get("memory", [])],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
        )

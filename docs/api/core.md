# Core API

## SuperOpt

Main optimizer class.

```python
class SuperOpt:
    def __init__(self,
                 environment: AgenticEnvironment | None = None,
                 alpha: float = 1.0,
                 use_stability_checks: bool = True)

    def step(self, trace: ExecutionTrace) -> None:
        """Perform optimization step"""

    def optimize_episode(self,
                        task_description: str,
                        agent_executor: callable,
                        max_iterations: int = 10) -> dict:
        """Run complete optimization episode"""

    def get_statistics(self) -> dict:
        """Get optimization statistics"""
```

## AgenticEnvironment

Agent environment container.

```python
@dataclass
class AgenticEnvironment:
    prompts: PromptConfig
    tools: dict[str, ToolSchema]
    retrieval: RetrievalConfig
    memory: list[MemoryEntry]

    def apply_update(self, nlg, alpha: float = 1.0) -> AgenticEnvironment:
        """Apply updates to environment"""

    def to_dict(self) -> dict:
        """Serialize to dictionary"""

    @classmethod
    def from_dict(cls, data: dict) -> AgenticEnvironment:
        """Deserialize from dictionary"""
```

## PromptConfig

Prompt configuration.

```python
@dataclass
class PromptConfig:
    system_prompt: str = ""
    instruction_policy: str = ""
    few_shot_exemplars: list[str] = field(default_factory=list)
    behavioral_constraints: list[str] = field(default_factory=list)
```

## ToolSchema

Tool definition.

```python
@dataclass
class ToolSchema:
    name: str
    description: str
    arguments: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
```

## RetrievalConfig

Retrieval settings.

```python
@dataclass
class RetrievalConfig:
    top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    rerank_threshold: float = 0.7
    mode: str = "semantic"
    query_rewrite_strategy: str = "default"
    file_type_filters: list[str] = field(default_factory=list)
    dependency_expansion_depth: int = 1
```

## MemoryEntry

Memory item.

```python
@dataclass
class MemoryEntry:
    entry_type: str
    content: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    helpful_count: int = 0
    harmful_count: int = 0

    def decay(self, lambda_decay: float, current_time: datetime) -> float:
        """Apply time-based decay"""
```

## ExecutionTrace

Execution record.

```python
@dataclass
class ExecutionTrace:
    task_description: str
    success: bool = False
    response: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_errors: list[ToolCall] = field(default_factory=list)
    failure_type: FailureType = FailureType.NONE
    metadata: dict[str, Any] = field(default_factory=dict)
```

## ToolCall

Tool execution record.

```python
@dataclass
class ToolCall:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error_message: str = ""
    execution_time: float = 0.0
```

## FailureType

Failure categories.

```python
class FailureType(Enum):
    PROMPT = "PROMPT"
    TOOL = "TOOL"
    RETRIEVAL = "RETRIEVAL"
    MEMORY = "MEMORY"
    NONE = "NONE"
```

## Usage Example

```python
from superopt import SuperOpt, AgenticEnvironment
from superopt.core.environment import PromptConfig, ToolSchema

# Create environment
env = AgenticEnvironment(
    prompts=PromptConfig(system_prompt="You are a helpful assistant."),
    tools={
        "edit_file": ToolSchema(
            name="edit_file",
            description="Edit files",
            arguments={"file": "str", "line": "int"}
        )
    }
)

# Create optimizer
optimizer = SuperOpt(environment=env)

# Optimize after failure
optimizer.step(execution_trace)
```
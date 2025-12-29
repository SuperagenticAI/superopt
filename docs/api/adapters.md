# Adapters API

## AgentAdapter Interface

Base interface for all agent adapters.

```python
class AgentAdapter(ABC):
    @abstractmethod
    def extract_environment(self) -> AgenticEnvironment:
        """Extract current environment from agent"""

    @abstractmethod
    def apply_environment(self, environment: AgenticEnvironment) -> None:
        """Apply environment to agent"""

    @abstractmethod
    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and return trace"""

    def get_agent_info(self) -> dict[str, Any]:
        """Get agent information"""

    def validate_environment(self, environment: AgenticEnvironment) -> bool:
        """Validate environment compatibility"""

    def health_check(self) -> dict[str, Any]:
        """Check adapter and agent health"""
```

## AiderAdapter

Adapter for Aider coding assistant.

```python
class AiderAdapter(AgentAdapter):
    def __init__(self,
                 aider_instance: Any = None,
                 model: str = "gpt-4",
                 auto_commits: bool = False,
                 **aider_kwargs)

    def extract_environment(self) -> AgenticEnvironment:
        """Extract environment from Aider"""

    def apply_environment(self, environment: AgenticEnvironment) -> None:
        """Apply environment to Aider"""

    def execute(self, task: str) -> ExecutionTrace:
        """Execute coding task with Aider"""

    def get_aider_tools(self) -> dict[str, ToolSchema]:
        """Get Aider tool schemas"""
```

## LettaAdapter

Adapter for Letta memory agents.

```python
class LettaAdapter(AgentAdapter):
    def __init__(self,
                 letta_agent: Any = None,
                 memory_bank_id: str = None,
                 **letta_kwargs)

    def extract_environment(self) -> AgenticEnvironment:
        """Extract environment from Letta"""

    def apply_environment(self, environment: AgenticEnvironment) -> None:
        """Apply environment to Letta"""

    def execute(self, task: str) -> ExecutionTrace:
        """Execute task with Letta"""

    def sync_memory(self) -> None:
        """Synchronize memory"""
```

## CodexAdapter

Adapter for Codex code generation.

```python
class CodexAdapter(AgentAdapter):
    def __init__(self,
                 codex_instance: Any = None,
                 model: str = "codex-davinci-002",
                 **codex_kwargs)

    def extract_environment(self) -> AgenticEnvironment:
        """Extract environment from Codex"""

    def apply_environment(self, environment: AgenticEnvironment) -> None:
        """Apply environment to Codex"""

    def execute(self, task: str) -> ExecutionTrace:
        """Execute code generation task"""
```

## Custom Adapter Template

```python
from superopt.adapters.base import AgentAdapter

class CustomAgentAdapter(AgentAdapter):
    def __init__(self, agent_instance, **kwargs):
        self.agent = agent_instance
        self.config = kwargs

    def extract_environment(self) -> AgenticEnvironment:
        """Extract environment from your agent"""
        return AgenticEnvironment(
            prompts=PromptConfig(system_prompt=self.agent.get_prompt()),
            tools=self._extract_tools(),
            retrieval=self._extract_retrieval(),
            memory=self._extract_memory()
        )

    def apply_environment(self, env: AgenticEnvironment):
        """Apply environment to your agent"""
        self.agent.set_prompt(env.prompts.system_prompt)
        # Apply tools, retrieval, memory...

    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and return trace"""
        result = self.agent.run(task)
        return ExecutionTrace(
            task_description=task,
            success=result['success'],
            response=result.get('response', ''),
            tool_calls=result.get('tool_calls', [])
        )
```

## Adapter Registry

Manage multiple adapters.

```python
class AdapterRegistry:
    def __init__(self):
        self.adapters = {}

    def register(self, name: str, adapter: AgentAdapter) -> None:
        """Register adapter"""

    def get_adapter(self, name: str) -> AgentAdapter:
        """Get registered adapter"""

    def list_adapters(self) -> list[str]:
        """List adapter names"""

    def health_check_all(self) -> dict[str, dict]:
        """Check all adapters"""
```

## Testing Utilities

```python
class AdapterTester:
    def test_basic_functionality(self) -> dict[str, bool]:
        """Test adapter functionality"""

    def test_environment_consistency(self) -> bool:
        """Test extract/apply consistency"""

    def benchmark_performance(self, iterations: int = 10) -> dict[str, float]:
        """Benchmark adapter performance"""
```

## Usage Example

```python
from superopt.adapters import AiderAdapter

# Create adapter
adapter = AiderAdapter(aider_instance=my_aider)

# Test functionality
tester = AdapterTester(adapter)
results = tester.test_basic_functionality()

# Use adapter
environment = adapter.extract_environment()
trace = adapter.execute("Fix bug in main.py")
```

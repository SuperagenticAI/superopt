# Integration Patterns

SuperOpt integrates with different agent frameworks through adapter interfaces.

## Adapter Interface

All adapters implement this consistent interface:

```python
class AgentAdapter(ABC):
    def extract_environment(self) -> AgenticEnvironment:
        """Get current agent environment"""

    def apply_environment(self, environment: AgenticEnvironment) -> None:
        """Apply optimized environment to agent"""

    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and return trace"""
```

## Built-in Adapters

### AiderAdapter

```python
from superopt.adapters import AiderAdapter

adapter = AiderAdapter(aider_instance=my_aider)
environment = adapter.extract_environment()
optimizer = SuperOpt(environment=environment)

trace = adapter.execute("Fix bug in main.py")
optimizer.step(trace)
adapter.apply_environment(optimizer.environment)
```

### LettaAdapter

```python
from superopt.adapters import LettaAdapter

adapter = LettaAdapter(letta_agent=my_letta)
environment = adapter.extract_environment()
optimizer = SuperOpt(environment=environment)

trace = adapter.execute("Research topic")
optimizer.step(trace)
adapter.apply_environment(optimizer.environment)
```

## Custom Integration

For agents not covered by built-in adapters:

```python
from superopt.adapters.base import AgentAdapter

class MyAgentAdapter(AgentAdapter):
    def __init__(self, agent):
        self.agent = agent

    def extract_environment(self) -> AgenticEnvironment:
        return AgenticEnvironment(
            prompts=PromptConfig(system_prompt=self.agent.get_prompt()),
            tools=self._extract_tools(),
            retrieval=self._extract_retrieval(),
            memory=self._extract_memory()
        )

    def apply_environment(self, env: AgenticEnvironment):
        self.agent.set_prompt(env.prompts.system_prompt)
        # Apply tools, retrieval, memory...

    def execute(self, task: str) -> ExecutionTrace:
        result = self.agent.run(task)
        return ExecutionTrace(
            task_description=task,
            success=result['success'],
            response=result.get('response', ''),
            tool_calls=result.get('tool_calls', [])
        )
```

## Integration Patterns

### Synchronous

Optimize immediately after each execution:

```python
optimizer = SuperOpt(environment)
trace = adapter.execute(task)
optimizer.step(trace)  # Immediate optimization
```

### Asynchronous

Background optimization:

```python
import asyncio

async def optimize_background():
    trace = await adapter.execute_async(task)
    optimizer.step(trace)  # Background processing
```

### Batch Processing

Accumulate traces and optimize together:

```python
traces = []
for task in tasks:
    trace = adapter.execute(task)
    traces.append(trace)

# Batch optimize
for trace in traces:
    if not trace.success:
        optimizer.step(trace)
```

## Health Monitoring

```python
health = adapter.health_check()
print(f"Adapter status: {health['status']}")
print(f"Agent status: {health['agent_status']}")
```

## Error Handling

```python
try:
    trace = adapter.execute(task)
    optimizer.step(trace)
except AdapterError as e:
    print(f"Integration error: {e}")
    # Fallback logic...
```
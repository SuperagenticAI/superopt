# 🔌 Integration Guide

SuperOpt integrates with autonomous agents through adapter patterns. This guide shows how to connect SuperOpt to different agent frameworks using real code examples.

## 🏗️ Integration Architecture

SuperOpt uses the **Adapter Pattern** to connect with agents:

```
Agent Framework → AgentAdapter → SuperOpt → Environment Updates
    ↓                    ↓              ↓
Real Agent        Standardized      Optimization
Execution         Interface         Engine
```

## 🔧 AgentAdapter Interface

All adapters implement the same interface:

```python
from superopt.adapters.base import AgentAdapter
from superopt.core.environment import AgenticEnvironment
from superopt.core.trace import ExecutionTrace

class AgentAdapter(ABC):
    @abstractmethod
    def extract_environment(self) -> AgenticEnvironment:
        """Extract current environment from agent."""
        pass

    @abstractmethod
    def apply_environment(self, env: AgenticEnvironment) -> None:
        """Apply optimized environment to agent."""
        pass

    @abstractmethod
    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and return trace."""
        pass
```

## 📚 Available Adapters

### Aider Adapter
For Aider code editing agents:

```python
from superopt.adapters import AiderAdapter
from superopt import SuperOpt

# Create adapter for Aider instance
adapter = AiderAdapter(
    model="gpt-4",                    # Model to use
    coder_class="EditBlockCoder",     # Aider coder type
    # Additional Aider configuration...
)

# Extract current environment
environment = adapter.extract_environment()

# Initialize optimizer
optimizer = SuperOpt(environment=environment)

# Run optimization episode
results = optimizer.optimize_episode(
    task_description="Fix the failing tests in auth.py",
    agent_executor=adapter.execute,
    max_iterations=10,
)

# Apply optimized environment
adapter.apply_environment(optimizer.environment)
```

### Letta Adapter
For Letta memory-enabled agents:

```python
from superopt.adapters import LettaAdapter
from superopt import SuperOpt

# Create adapter for Letta agent
adapter = LettaAdapter(
    agent_id="letta-agent-001",
    # Letta-specific configuration...
)

# Extract environment with memory
environment = adapter.extract_environment()

# Initialize optimizer
optimizer = SuperOpt(environment=environment)

# Optimize episode
results = optimizer.optimize_episode(
    task_description="Help user organize their project",
    agent_executor=adapter.execute,
    max_iterations=5,
)

# Apply improvements
adapter.apply_environment(optimizer.environment)
```

### Codex Adapter
For code understanding and retrieval agents:

```python
from superopt.adapters import CodexAdapter
from superopt import SuperOpt

# Create adapter for Codex agent
adapter = CodexAdapter(
    codebase_path="/path/to/project",
    model="gpt-4",
    # Codex-specific configuration...
)

# Extract environment
environment = adapter.extract_environment()

# Initialize optimizer
optimizer = SuperOpt(environment=environment)

# Run optimization
results = optimizer.optimize_episode(
    task_description="Explain how authentication works",
    agent_executor=adapter.execute,
    max_iterations=8,
)

# Apply optimized environment
adapter.apply_environment(optimizer.environment)
```

## 🛠️ Custom Agent Integration

For agents not covered by existing adapters:

```python
from superopt.adapters.base import AgentAdapter
from superopt.core.environment import AgenticEnvironment, PromptConfig, ToolSchema
from superopt.core.trace import ExecutionTrace, FailureType, ToolCall
from superopt import SuperOpt

class MyCustomAdapter(AgentAdapter):
    def __init__(self, my_agent):
        self.agent = my_agent

    def extract_environment(self) -> AgenticEnvironment:
        """Extract current environment from your agent."""
        return AgenticEnvironment(
            prompts=PromptConfig(
                system_prompt=self.agent.get_system_prompt(),
                instruction_policy=self.agent.get_instructions(),
            ),
            tools={
                name: ToolSchema(
                    name=name,
                    description=tool.description,
                    arguments=tool.parameters,
                )
                for name, tool in self.agent.get_tools().items()
            },
            retrieval=self.agent.get_retrieval_config(),
            memory=self.agent.get_memory_entries(),
        )

    def apply_environment(self, env: AgenticEnvironment) -> None:
        """Apply optimized environment back to agent."""
        # Update prompts
        self.agent.set_system_prompt(env.prompts.system_prompt)
        self.agent.set_instructions(env.prompts.instruction_policy)

        # Update tools
        tool_dict = {}
        for name, schema in env.tools.items():
            tool_dict[name] = {
                "description": schema.description,
                "parameters": schema.arguments,
            }
        self.agent.set_tools(tool_dict)

        # Update retrieval and memory
        self.agent.set_retrieval_config(env.retrieval)
        self.agent.set_memory_entries(env.memory)

    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and capture trace."""
        # Run the task
        result = self.agent.run(task)

        # Create execution trace
        trace = ExecutionTrace(task_description=task)

        # Mark success/failure
        trace.success = result.get("success", False)

        # Capture tool calls
        if "tool_calls" in result:
            for call in result["tool_calls"]:
                trace.tool_calls.append(ToolCall(
                    tool_name=call["name"],
                    arguments=call["arguments"],
                ))

        # Determine failure type (simplified)
        if not trace.success and trace.tool_calls:
            trace.failure_type = FailureType.TOOL
        elif not trace.success:
            trace.failure_type = FailureType.PROMPT
        else:
            trace.failure_type = FailureType.NONE

        return trace

# Usage
adapter = MyCustomAdapter(my_agent_instance)
environment = adapter.extract_environment()
optimizer = SuperOpt(environment=environment)

# Optimize
results = optimizer.optimize_episode(
    task_description="Help user with their task",
    agent_executor=adapter.execute,
    max_iterations=5,
)

# Apply improvements
adapter.apply_environment(optimizer.environment)
```

## ⚙️ Configuration Options

### SuperOpt Configuration
```python
from superopt import SuperOpt

optimizer = SuperOpt(
    environment=environment,
    max_iterations=10,           # Maximum optimization cycles
    stability_threshold=0.8,     # Stability requirement
    use_llm_diagnosis=True,      # Use LLM for failure diagnosis
    llm_client=my_llm_client,    # LLM client for diagnosis
)
```

### Environment Configuration
```python
from superopt.core.environment import AgenticEnvironment, PromptConfig

environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are a helpful assistant.",
        instruction_policy="Always be concise and accurate.",
        few_shot_exemplars=["Example 1", "Example 2"],
    ),
    tools={},  # Will be populated by adapter
    retrieval=None,  # Will be populated by adapter
    memory=[],  # Will be populated by adapter
)
```

## 🔄 Optimization Workflow

### Episode-Based Optimization
```python
# Run optimization episode
results = optimizer.optimize_episode(
    task_description="User's specific task",
    agent_executor=adapter.execute,
    max_iterations=10,
    convergence_threshold=0.9,
)

# Results contain optimization history
print(f"Converged after {results.iterations} iterations")
print(f"Final stability: {results.stability_score}")
```

### Single-Step Optimization
```python
# For single failure optimization
trace = adapter.execute("User task that failed")
optimizer.step(trace)  # Apply single optimization step
```

## 🐛 Troubleshooting

### Common Issues

**Adapter Not Extracting Environment**
- Ensure agent provides all required configuration
- Check that adapter methods return correct data types

**Optimization Not Improving Performance**
- Verify execution traces capture actual failures
- Check that environment updates are applied correctly
- Ensure agent can use updated configurations

**Integration Errors**
- Validate adapter interface implementation
- Check data type compatibility
- Verify agent can accept environment updates

### Debugging Tips
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test adapter independently
environment = adapter.extract_environment()
print(f"Extracted {len(environment.tools)} tools")

# Test single execution
trace = adapter.execute("Test task")
print(f"Success: {trace.success}, Failure: {trace.failure_type}")

# Apply and verify updates
adapter.apply_environment(environment)
# Verify agent behavior changed
```

## 📊 Monitoring Integration

### Performance Tracking
```python
# Track optimization metrics
results = optimizer.optimize_episode(
    task_description=task,
    agent_executor=adapter.execute,
)

# Log performance
print(f"Optimization completed in {results.iterations} steps")
print(f"Stability achieved: {results.stability_score > 0.8}")
print(f"Environment updated: {len(results.updates_applied)} changes")
```

This integration approach makes SuperOpt compatible with any autonomous agent framework while providing comprehensive environment optimization capabilities.

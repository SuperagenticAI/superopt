# 🚀 Examples

Real code examples showing how to use SuperOpt with different scenarios. These examples are based on the actual implementation in the `examples/` directory.

## 📖 Basic Usage Example

This example demonstrates the complete SuperOpt workflow using the actual code from `examples/basic_example.py`:

```python
from superopt import AgenticEnvironment, ExecutionTrace, FailureType, SuperOpt
from superopt.core.environment import PromptConfig, RetrievalConfig, ToolSchema
from superopt.core.trace import ToolCall

# 1. Set up your agent environment
environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are a helpful coding assistant.",
    ),
    tools={
        "edit_file": ToolSchema(
            name="edit_file",
            description="Edit a file by applying changes",
            arguments={"file": "str", "line": "int"},
            required_fields=["file", "line"],
        ),
    },
    retrieval=RetrievalConfig(),
)

# 2. Initialize the SuperOpt optimizer
optimizer = SuperOpt(
    environment=environment,
    alpha=1.0,                    # Update acceptance rate
    use_stability_checks=True,    # Enable stability validation
)

print("Initial tool description:")
print(environment.tools['edit_file'].description)

# 3. Simulate agent execution with a failure
trace = ExecutionTrace(
    task_description="Edit line 0 in test.py",
    success=False,
)

# Add tool error (real example: line numbering issue)
trace.tool_errors.append(
    ToolCall(
        tool_name="edit_file",
        arguments={"file": "test.py", "line": 0},
        success=False,
        error_message="Line numbers must be 1-indexed, not 0-indexed",
    )
)
trace.failure_type = FailureType.TOOL

# 4. Run optimization
optimizer.step(trace)

# 5. Check the improved environment
print("\nOptimized tool description:")
print(optimizer.environment.tools['edit_file'].description)
# Output: "Edit a file by applying changes. Note: Line numbers must be 1-indexed..."
```

## 🏃 Running the Example

```bash
# From the project root
python examples/basic_example.py
```

Expected output:
```
SuperOpt Basic Example
==================================================

1. Initial Environment:
   Tool schema description: Edit a file by applying changes...

2. Executing task with tool error...
   Error: Line numbers must be 1-indexed, not 0-indexed

3. Optimizing environment...

4. Updated Environment:
   Tool schema description length: 85 chars
   ✓ Schema was updated with clarifications

5. Statistics:
   Controller diagnoses: {'TOOL': 1, 'PROMPT': 0, 'RETRIEVAL': 0, 'MEMORY': 0, 'NONE': 0}
   Optimization steps: 1

==================================================
Example completed!
```

## 🔧 Integration Examples

### With Aider (Code Editing Agent)

```python
from superopt.adapters import AiderAdapter
from superopt import SuperOpt

# Connect to Aider instance
adapter = AiderAdapter(
    model="gpt-4",
    coder_class="EditBlockCoder",
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

# Apply optimized environment back to Aider
adapter.apply_environment(optimizer.environment)
```

### With Custom Agent

```python
from superopt.adapters.base import AgentAdapter
from superopt import SuperOpt

class MyAgentAdapter(AgentAdapter):
    def __init__(self, agent):
        self.agent = agent

    def extract_environment(self):
        return AgenticEnvironment(
            prompts=PromptConfig(system_prompt=self.agent.config.prompt),
            tools=self.agent.get_tool_schemas(),
            retrieval=self.agent.get_retrieval_config(),
            memory=self.agent.get_memory(),
        )

    def apply_environment(self, env):
        self.agent.config.prompt = env.prompts.system_prompt
        self.agent.set_tool_schemas(env.tools)
        self.agent.set_retrieval_config(env.retrieval)
        self.agent.set_memory(env.memory)

    def execute(self, task):
        result = self.agent.run(task)
        # Convert to ExecutionTrace...
        return self._convert_to_trace(result)

# Usage
adapter = MyAgentAdapter(my_agent)
environment = adapter.extract_environment()
optimizer = SuperOpt(environment=environment)

# Optimize
results = optimizer.optimize_episode(
    task_description="Help user organize their project",
    agent_executor=adapter.execute,
    max_iterations=5,
)

adapter.apply_environment(optimizer.environment)
```

## 🎯 Optimization Scenarios

### Tool Schema Repair

**Problem**: Agent repeatedly fails with the same tool error

```python
# Agent keeps using 0-indexed line numbers
trace = ExecutionTrace(
    task_description="Edit the main function",
    success=False
)
trace.tool_errors.append(ToolCall(
    tool_name="edit_file",
    arguments={"file": "main.py", "line": 0},
    error_message="Line numbers must be 1-indexed"
))
trace.failure_type = FailureType.TOOL

optimizer.step(trace)
# Result: Tool schema updated with "Note: Line numbers are 1-indexed"
```

### Prompt Optimization

**Problem**: Agent misunderstands task requirements

```python
trace = ExecutionTrace(
    task_description="Create a REST API endpoint",
    success=False
)
# Agent creates incorrect implementation
trace.failure_type = FailureType.PROMPT

optimizer.step(trace)
# Result: Prompt updated with clearer API development instructions
```

### Retrieval Tuning

**Problem**: Agent can't find relevant information

```python
trace = ExecutionTrace(
    task_description="How does authentication work?",
    success=False
)
# Agent searches but finds irrelevant results
trace.failure_type = FailureType.RETRIEVAL

optimizer.step(trace)
# Result: Retrieval parameters optimized for better search results
```

### Memory Conflicts

**Problem**: Agent repeats previously learned mistakes

```python
trace = ExecutionTrace(
    task_description="Process user data",
    success=False
)
# Agent forgets GDPR compliance rules
trace.failure_type = FailureType.MEMORY

optimizer.step(trace)
# Result: Memory updated with correct compliance rules
```

## ⚙️ Configuration Examples

### Basic Configuration

```python
optimizer = SuperOpt(
    environment=environment,
    alpha=1.0,                      # Full update acceptance
    use_stability_checks=True,      # Validate updates
)
```

### Advanced Configuration

```python
optimizer = SuperOpt(
    environment=environment,
    alpha=0.8,                      # Conservative updates
    use_stability_checks=True,
    max_iterations_per_step=3,      # Limit optimization depth
    use_llm_diagnosis=True,         # Use LLM for failure analysis
    llm_client=my_llm_client,
)
```

### Component-Specific Configuration

```python
# Custom SuperPrompt configuration
superprompt = SuperPrompt(
    population_size=20,
    max_generations=10,
    mutation_rate=0.3,
)

# Custom SuperRAG configuration
superrag = SuperRAG(
    max_top_k=100,
    min_top_k=1,
)

# Integrate with SuperOpt
optimizer = SuperOpt(
    environment=environment,
    superprompt=superprompt,
    superrag=superrag,
)
```

## 📊 Monitoring Examples

### Track Optimization Progress

```python
results = optimizer.optimize_episode(
    task_description="Complex coding task",
    agent_executor=adapter.execute,
    max_iterations=10,
)

print(f"Converged in {results.iterations} iterations")
print(f"Stability score: {results.stability_score}")
print(f"Components optimized: {len(results.component_updates)}")
```

### Statistics Tracking

```python
# Get current statistics
stats = optimizer.get_statistics()
print("Failure types diagnosed:")
for failure_type, count in stats['controller_stats'].items():
    print(f"  {failure_type}: {count}")

print(f"Total optimization steps: {stats['optimization_steps']}")
```

These examples demonstrate real SuperOpt usage patterns based on the actual implementation. Start with the basic example and progress to more complex integration scenarios.

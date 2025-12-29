# Quick Start

## Basic Usage

```python
from superopt import SuperOpt, AgenticEnvironment
from superopt.core.environment import PromptConfig, ToolSchema

# Set up your agent environment
environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are a helpful coding assistant."
    ),
    tools={
        "edit_file": ToolSchema(
            name="edit_file",
            description="Edit a file by applying changes",
            arguments={"file": "str", "line": "int"},
        ),
    },
)

# Create optimizer
optimizer = SuperOpt(environment=environment)

# After your agent fails, optimize
optimizer.step(execution_trace)
```

## Example with Aider

```python
from superopt.adapters import AiderAdapter

# Connect to Aider
adapter = AiderAdapter(aider_instance=my_aider)
environment = adapter.extract_environment()
optimizer = SuperOpt(environment=environment)

# Run task and optimize
trace = adapter.execute("Fix the bug in main.py")
optimizer.step(trace)
adapter.apply_environment(optimizer.environment)
```

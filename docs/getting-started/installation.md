# 🚀 Getting Started

## 📦 Installation

### Basic Installation

```bash
pip install superopt
```

### Development Installation

```bash
git clone https://github.com/SuperagenticAI/superopt.git
cd superopt
pip install -e .
```

### Optional Dependencies

```bash
# Development tools (pytest, black, ruff)
pip install -e ".[dev]"

# Aider integration (for coding agent optimization)
pip install -e ".[aider]"

# LanceDB for RAG optimization
pip install -e ".[lancedb]"

# All optional dependencies
pip install -e ".[all]"
```

### Requirements

- Python 3.12+
- Basic dependencies: pydantic

## 🚀 Quick Start

### Basic Usage - How SuperOpt Learns and Improves

> **Note:** This is a simplified demo to show SuperOpt's core concept. The same approach works for complex, real-world agents with multiple tools, advanced prompts, and sophisticated workflows.

This example demonstrates how SuperOpt automatically detects a tool schema issue, analyzes the failure, and updates the environment to prevent future errors. In a real agent, you'd capture traces from actual user interactions or complex tasks.

> **More Examples Coming Soon:** We'll soon publish comprehensive examples showing SuperOpt with multi-tool agents, conversation flows, code generation, data analysis, and enterprise integrations.

### Step 1: Import Required Modules

```python
from superopt import SuperOpt, AgenticEnvironment
from superopt.core.environment import PromptConfig, ToolSchema
from superopt.core.trace import ExecutionTrace, ToolCall
```

### Step 2: Define Your Agent's Environment

*This creates a complete specification of how your AI agent should behave*

```python
environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are a helpful coding assistant."
    ),
    tools={
        "edit_file": ToolSchema(
            name="edit_file",
            description="Edit a file at a specific line",
            arguments={"file": "str", "line": "int"},
        ),
    },
)
```

### Step 3: Initialize SuperOpt Optimizer

*This creates an intelligent system that can observe, learn, and improve your agent*

```python
optimizer = SuperOpt(environment=environment)
```

### Step 4: Capture Agent Execution Trace

*When your agent tries to edit line 0 and fails, you create a "trace" of what happened*

```python
trace = ExecutionTrace(
    task_description="Edit line 0 in test.py",
    success=False,
)
trace.tool_errors.append(ToolCall(
    tool_name="edit_file",
    arguments={"file": "test.py", "line": 0},
    error_message="Line numbers must be 1-indexed",
))
```

### Step 5: Let SuperOpt Learn and Optimize

*SuperOpt analyzes the failure and updates the environment*

```python
optimizer.step(trace)
```

### Step 6: Check the Improved Environment

```python
print(optimizer.environment.tools['edit_file'].description)
```

**Expected Output:**
```
Edit a file at a specific line

**IMPORTANT CONSTRAINTS:**
- CRITICAL: Line numbers and indices are 1-indexed, not 0-indexed.
```

## What Just Happened?

**Behind the scenes, SuperOpt:**

1. **SuperController** analyzed the trace and determined this is a TOOL failure
2. **SuperReflexion** was activated to repair the tool schema
3. The error message "Line numbers must be 1-indexed" was analyzed
4. Tool schema was updated with the 1-indexing constraint
5. Now your agent knows lines start from 1, not 0!

## Complete Working Example

Here's the complete, runnable program you can copy and test:

```python
# Complete SuperOpt Example - Copy this entire file to test SuperOpt
from superopt import SuperOpt, AgenticEnvironment
from superopt.core.environment import PromptConfig, ToolSchema
from superopt.core.trace import ExecutionTrace, ToolCall

# 1. Define your agent's environment
environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are a helpful coding assistant."
    ),
    tools={
        "edit_file": ToolSchema(
            name="edit_file",
            description="Edit a file at a specific line",
            arguments={"file": "str", "line": "int"},
        ),
    },
)

# 2. Initialize the optimizer
optimizer = SuperOpt(environment=environment)

# 3. Simulate agent execution with a failure
trace = ExecutionTrace(
    task_description="Edit line 0 in test.py",
    success=False,
)
trace.tool_errors.append(ToolCall(
    tool_name="edit_file",
    arguments={"file": "test.py", "line": 0},
    error_message="Line numbers must be 1-indexed",
))

# 4. Let SuperOpt learn and optimize
print("Before optimization:")
print(optimizer.environment.tools['edit_file'].description)
print()

optimizer.step(trace)

# 5. Check the improved environment
print("After optimization:")
print(optimizer.environment.tools['edit_file'].description)
```

**To test this example:**
1. Save the code above as `test_superopt.py`
2. Run `python test_superopt.py`
3. You should see the tool description get updated with the 1-indexing constraint

## Run the Official Example

You can also run the official example included with SuperOpt:

```bash
python examples/basic_example.py
```

**Expected Output:**
```
SuperOpt Basic Example
==================================================

1. Initial Environment:
   Tool schema description: Edit a file by applying changes...

2. Executing task with tool error...
   Error: Line numbers must be 1-indexed, not 0-indexed

3. Optimizing environment...

4. Updated Environment:
   Tool schema description length: 126 chars
   ✓ Schema was updated with clarifications

5. Statistics:
   Controller diagnoses: {'PROMPT': 0, 'TOOL': 1, 'RETRIEVAL': 0, 'MEMORY': 0, 'NONE': 0}
   Optimization steps: 1

==================================================
Example completed!
```

The official example demonstrates the complete SuperOpt workflow and shows how tool schemas get automatically updated with learned constraints.

> **💡 Apply to Real Agents:** This same pattern works for any agent! Capture traces from user conversations, API calls, code generation, data analysis, or any task where your agent might fail or need improvement. SuperOpt will continuously learn and optimize.

## Scaling to Production Agents

While this example uses a simple tool, SuperOpt works with complex, real-world agents:

### Real Agent Integration
```python
# Example: Integrating with a coding assistant agent
environment = AgenticEnvironment(
    prompts=PromptConfig(
        system_prompt="You are an expert software engineer...",
        user_prompt_template="Help me with: {task}",
    ),
    tools={
        "run_terminal": ToolSchema(...),
        "read_file": ToolSchema(...),
        "search_code": ToolSchema(...),
        "run_tests": ToolSchema(...),
        # ... 20+ tools for comprehensive coding assistance
    },
    retrieval=RetrievalConfig(...),  # For codebase search
    memory=MemoryConfig(...)         # For conversation context
)

optimizer = SuperOpt(environment)
# Every coding session, user interaction, or CI/CD failure becomes a learning opportunity
```

### Continuous Learning
SuperOpt learns from:
- **User feedback** ("That wasn't quite right...")
- **Tool failures** (API errors, permission issues, format problems)
- **Performance metrics** (response time, accuracy, user satisfaction)
- **Success patterns** (what works well gets reinforced)

> **Coming Soon:** Production-ready examples with popular agent frameworks like CrewAI, AutoGen, and custom enterprise agents.

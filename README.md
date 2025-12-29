<div align="center">
  <img src="https://raw.githubusercontent.com/SuperagenticAI/superopt/main/assets/SuperOpt_logo.png" alt="SuperOpt Logo" width="400" height="auto">

  # 🚀 SuperOpt

  **Agentic Environment Optimization for Autonomous AI Agents**

  <p>
    <a href="https://pypi.org/project/superopt/"><img src="https://img.shields.io/pypi/v/superopt.svg" alt="PyPI"></a>
    <a href="https://github.com/SuperagenticAI/superopt/actions"><img src="https://github.com/SuperagenticAI/superopt/workflows/CI/badge.svg" alt="CI"></a>
    <a href="https://github.com/SuperagenticAI/superopt/blob/main/LICENSE"><img src="https://img.shields.io/github/license/SuperagenticAI/superopt.svg" alt="License"></a>
    <a href="https://github.com/SuperagenticAI/superopt/stargazers"><img src="https://img.shields.io/github/stars/SuperagenticAI/superopt.svg" alt="GitHub stars"></a>
  </p>

  <p align="center">
    <em>SuperOpt is a unified framework for optimizing agent environments (prompts, tools, retrieval, memory) without modifying model parameters. It treats the entire agent environment as a structured optimization target, enabling autonomous agents to self-correct and stabilize over time.</em>
  </p>
</div>

---

## ✨ Key Features

<div align="center">

| 🚀 **Environment-Level Optimization** | 🎯 **Automatic Failure Diagnosis** | 🛡️ **Stability Guarantees** |
|:-------------------------------------:|:----------------------------------:|:----------------------------:|
| Optimize prompts, tools, retrieval, and memory as a unified system | Intelligent routing of failures to appropriate optimizers | Hierarchy of mutability prevents oscillation and ensures convergence |

| 📊 **Trace-Based Learning** | ⚡ **No Model Retraining** | 🔧 **Framework Agnostic** |
|:--------------------------:|:-------------------------:|:-------------------------:|
| Uses execution traces as supervision signals | All improvements happen at the environment level | Works with DSPy, CrewAI, AutoGen, and custom agents |

</div>

## 🏗️ Architecture Overview

SuperOpt formalizes optimization as iterative descent over **Natural Language Gradients** derived from execution traces. A meta-diagnostic controller attributes failures to specific environment layers and routes corrective updates to specialized optimization engines.

### Core Components

<div align="center">

| 🎯 **SuperController** | 📝 **SuperPrompt** | 🔧 **SuperReflexion** | 🔍 **SuperRAG** | 🧠 **SuperMem** |
|:----------------------:|:------------------:|:----------------------:|:----------------:|:---------------:|
| Diagnostic meta-controller for failure routing | Evolutionary instruction optimization (GEPA-based) | Self-healing tool schema repair | Adaptive retrieval optimization | Typed memory with decay and conflict resolution |

</div>

## Research Paper

The research paper describing SuperOpt has been uploaded and will be available soon after launch.

## Key Features

- **Environment-Level Optimization**: Optimize prompts, tools, retrieval, and memory as a unified system
- **Failure Attribution**: Automatic diagnosis and routing of failures to appropriate optimizers
- **Stability Guarantees**: Hierarchy of mutability prevents oscillation and ensures convergence
- **Trace-Based Learning**: Uses execution traces as supervision signals
- **No Model Retraining**: All improvements happen at the environment level

## 📦 Installation

### Quick Install

```bash
pip install superopt
```

### From Source

```bash
git clone https://github.com/SuperagenticAI/superopt.git
cd superopt
pip install -e .
```

### Optional Dependencies

<div align="center">

| Feature | Install Command | Description |
|:-------:|:---------------:|:-----------:|
| 🧪 **Development** | `pip install -e ".[dev]"` | Testing, linting, formatting tools |
| 🤖 **Aider Integration** | `pip install -e ".[aider]"` | Coding agent optimization |
| 🔍 **LanceDB RAG** | `pip install -e ".[lancedb]"` | Vector database for retrieval |
| 📦 **Everything** | `pip install -e ".[all]"` | All optional dependencies |

</div>

## ⚡ Quick Start

### 🚀 Try It Now

<div align="center">

**Copy and run this complete example:**

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

</div>

### 🏃‍♂️ Run the Official Example

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
```

## 🔄 How SuperOpt Works

SuperOpt operates in an **outer optimization loop** surrounding the agent execution loop:

<div align="center">

```
┌─────────────────────────────────────────────────────────────┐
│                    🚀 SuperOpt Optimization Loop             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  🤖 Agent Execution Loop                 ││
│  │   Task → Agent → Tool Calls → Results → Output          ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│                    📊 Execution Trace                        │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              🎯 SuperController (Diagnosis)              ││
│  │   Classify failure: PROMPT | TOOL | RETRIEVAL | MEMORY  ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         ↓                 ↓                 ↓               │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│   │📝 Super- │     │🔧 Super-   │     │🔍 Super- │           │
│   │   Prompt │     │ Reflexion │     │   RAG   │           │
│   │(Prompts) │     │  (Tools)  │     │(Retrieval)│          │
│   └──────────┘     └──────────┘     └──────────┘           │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ↓                                  │
│              🌟 Natural Language Gradient (∇_NL)            │
│                           ↓                                  │
│                  ✨ Updated Environment Φ                   │
└─────────────────────────────────────────────────────────────┘
```

</div>

### 📋 Optimization Workflow

<div align="center">

| Step | Action | Description |
|:----:|:------:|:-----------:|
| 1️⃣ | **Execute** | Run agent task under current environment |
| 2️⃣ | **Capture** | Record structured execution trace |
| 3️⃣ | **Diagnose** | SuperController classifies the failure mode |
| 4️⃣ | **Route** | Send trace to the appropriate optimizer |
| 5️⃣ | **Generate** | Create Natural Language Gradient update |
| 6️⃣ | **Validate** | Check update against stability constraints |
| 7️⃣ | **Apply** | Update environment and persist |
| 8️⃣ | **Repeat** | Continue until convergence |

</div>

## 🧩 Core Components

### 🎯 SuperController
**Diagnostic Meta-Controller**

The intelligent orchestrator that analyzes execution traces and routes optimization tasks to the appropriate component:

- **PROMPT**: Handles instruction violations, format errors, and unclear prompts
- **TOOL**: Detects schema violations, invalid arguments, and tool misuse
- **RETRIEVAL**: Identifies missing symbols, empty results, and retrieval failures
- **MEMORY**: Catches repeated mistakes, contradictions, and memory issues

### 📝 SuperPrompt
**Evolutionary Prompt Optimizer**

Advances prompt engineering through systematic optimization:

- Reflective mutation guided by execution traces and failure patterns
- Pareto-based selection across multiple objectives (accuracy, efficiency, clarity)
- Population-based search using GEPA methodology for prompt evolution
- Automatic prompt refinement based on real-world performance data

### 🔧 SuperReflexion
**Self-Healing Tool Schemas**

Automatically repairs and enhances tool definitions when agents encounter issues:

- Analyzes tool failures and error patterns in real-time
- Generates schema clarifications and constraint additions automatically
- Appends important constraints to tool descriptions to prevent future errors
- Learns from agent mistakes to improve tool reliability

### 🔍 SuperRAG
**Adaptive Retrieval Optimization**

Dynamically optimizes retrieval-augmented generation systems:

- Optimizes `top_k` retrieval count based on query complexity and context
- Adapts chunk size and overlap for better semantic understanding
- Tunes reranking thresholds to improve result relevance
- Automatically switches between semantic vs structural retrieval modes

### 🧠 SuperMem
**Intelligent Memory System**

Advanced memory management with hierarchical organization:

- **Type hierarchy**: TOOL_RULE > RAG_HEURISTIC > STRATEGY for organized knowledge
- **Exponential decay**: Relevance-based forgetting to maintain current knowledge
- **Conflict resolution**: Automatic detection and resolution of contradictory information
- **Confidence tracking**: Validation and uncertainty quantification for memory entries

## Integration with Agents

SuperOpt provides adapters for popular agent frameworks:

### Using with Aider

```python
from superopt.adapters import AiderAdapter
from superopt import SuperOpt

# Create adapter for your Aider instance
adapter = AiderAdapter(
    model="gpt-4",
    coder_class="EditBlockCoder",
)

# Extract the current environment
environment = adapter.extract_environment()

# Initialize optimizer
optimizer = SuperOpt(environment=environment)

# Run optimization episode
results = optimizer.optimize_episode(
    task_description="Fix the failing tests in auth.py",
    agent_executor=adapter.execute,
    max_iterations=10,
)

# Apply optimized environment back to agent
adapter.apply_environment(optimizer.environment)
```

### Custom Agent Integration

```python
from superopt.adapters.base import AgentAdapter
from superopt import AgenticEnvironment, ExecutionTrace

class MyAgentAdapter(AgentAdapter):
    def extract_environment(self) -> AgenticEnvironment:
        """Extract current environment from your agent."""
        return AgenticEnvironment(
            prompts=self.agent.get_prompts(),
            tools=self.agent.get_tools(),
        )

    def apply_environment(self, env: AgenticEnvironment) -> None:
        """Apply optimized environment back to agent."""
        self.agent.set_prompts(env.prompts)
        self.agent.set_tools(env.tools)

    def execute(self, task: str) -> ExecutionTrace:
        """Execute task and return trace."""
        result = self.agent.run(task)
        return self._create_trace(result)
```

## 📊 Evaluation & Benchmarks

### 🏃‍♂️ Run Evaluations

```bash
# Quick evaluation on sample tasks
python scripts/evaluate_baseline.py --tasks data/tasks/sample_tasks.json
python scripts/evaluate_superopt.py --tasks data/tasks/sample_tasks.json
python scripts/compare_all.py --tasks data/tasks/sample_tasks.json

# Analyze results
python scripts/analyze_results.py --results-dir results/
```



## 📈 Evaluation Metrics

SuperOpt evaluates improvements across multiple dimensions:

<div align="center">

| 🔒 **Reliability** | 🛡️ **Stability** | ⚡ **Efficiency** | 🌍 **Generalization** | 👁️ **Interpretability** |
|:------------------:|:----------------:|:----------------:|:---------------------:|:-----------------------:|
| Reduction in repeated failures | Persistence of improvements over time | Token usage, retry counts | Transfer across tasks | Human-readable updates |

</div>

## 🔬 Related Research

SuperOpt builds upon groundbreaking work in agent optimization:

<div align="center">

| 🎯 **GEPA** | 🧠 **ACE** | 🎓 **Meta-ACE** | 🔧 **DSPy** | 📝 **TextGrad** |
|:-----------:|:----------:|:---------------:|:-----------:|:--------------:|
| Evolutionary prompt optimization | Agentic context engineering | Meta-reasoning extensions | Prompt programming framework | Textual differentiation |

*Agrawal et al. (2025) • Zhang et al. (2025) • Romero (2025) • Khattab et al. (2023) • Yuksekgonul et al. (2024)*

</div>

## 🤝 Contributing

<div align="center">

**We welcome contributions!** Here's how to get started:

</div>

### 🚀 Quick Start

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### 🛠️ Development Setup

```bash
git clone https://github.com/SuperagenticAI/superopt.git
cd superopt
pip install -e ".[dev]"

# Run tests and quality checks
pytest
black .
ruff check .
```

---

<div align="center">

## 📄 License

**Apache License 2.0** - see [LICENSE](LICENSE) file for details.

## 🤝 Support & Community

<div align="center">

| 📧 **Email** | 🐛 **Issues** | 💬 **Discussions** | 🌟 **Contribute** |
|:------------:|:-------------:|:------------------:|:----------------:|
| shashi@super-agentic.ai | [GitHub Issues](https://github.com/SuperagenticAI/superopt/issues) | [GitHub Discussions](https://github.com/SuperagenticAI/superopt/discussions) | [Contributing Guide](CONTRIBUTING.md) |

</div>

---

<div align="center">

**Brought to you 🔥 by [Superagentic AI](https://super-agentic.ai/)**

<img src="https://img.shields.io/github/last-commit/SuperagenticAI/superopt.svg" alt="Last commit"> <img src="https://img.shields.io/github/issues/SuperagenticAI/superopt.svg" alt="Issues"> <img src="https://img.shields.io/github/issues-pr/SuperagenticAI/superopt.svg" alt="Pull requests">

</div>

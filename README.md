# SuperOpt: Agentic Environment Optimization for Autonomous AI Agents

**SuperOpt** is a unified framework for optimizing agent environments (prompts, tools, retrieval, memory) without modifying model parameters. It treats the entire agent environment as a structured optimization target, enabling autonomous agents to self-correct and stabilize over time.

## Overview

SuperOpt formalizes optimization as iterative descent over **Natural Language Gradients** derived from execution traces. A meta-diagnostic controller attributes failures to specific environment layers and routes corrective updates to specialized optimization engines:

- **SuperController**: Diagnostic meta-controller for failure routing
- **SuperPrompt**: Evolutionary instruction optimization (GEPA-based)
- **SuperReflexion**: Self-healing tool schema repair
- **SuperRAG**: Adaptive retrieval optimization
- **SuperMem**: Typed memory with decay and conflict resolution

## Key Features

- **Environment-Level Optimization**: Optimize prompts, tools, retrieval, and memory as a unified system
- **Failure Attribution**: Automatic diagnosis and routing of failures to appropriate optimizers
- **Stability Guarantees**: Hierarchy of mutability prevents oscillation and ensures convergence
- **Trace-Based Learning**: Uses execution traces as supervision signals
- **No Model Retraining**: All improvements happen at the environment level

## Installation

### Basic Installation

```bash
pip install superopt
```

### Install from Source

```bash
git clone https://github.com/SuperagenticAI/superopt.git
cd superopt
pip install -e .
```

### Optional Dependencies

```bash
# Development tools (pytest, black, ruff, mypy)
pip install -e ".[dev]"

# Aider integration (for coding agent optimization)
pip install -e ".[aider]"

# LanceDB for RAG optimization
pip install -e ".[lancedb]"

# All optional dependencies
pip install -e ".[all]"
```

## Quick Start

### Basic Usage

```python
from superopt import SuperOpt, AgenticEnvironment, ExecutionTrace
from superopt.core.environment import PromptConfig, ToolSchema
from superopt.core.trace import ToolCall, FailureType

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

# 3. After your agent fails, create a trace
trace = ExecutionTrace(
    task_description="Edit line 0 in test.py",
    success=False,
)
trace.tool_errors.append(ToolCall(
    tool_name="edit_file",
    arguments={"file": "test.py", "line": 0},
    error_message="Line numbers must be 1-indexed",
))
trace.failure_type = FailureType.TOOL

# 4. Optimize - SuperOpt will fix the tool schema
optimizer.step(trace)

# 5. The environment is now updated
print(optimizer.environment.tools['edit_file'].description)
# Output: "Edit a file at a specific line. Note: Line numbers must be 1-indexed, not 0-indexed."
```

### Run the Example

```bash
python examples/basic_example.py
```

## Architecture

SuperOpt operates in an outer optimization loop surrounding the agent execution loop:

```
┌─────────────────────────────────────────────────────────────┐
│                    SuperOpt Optimization Loop                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  Agent Execution Loop                    ││
│  │   Task → Agent → Tool Calls → Results → Output          ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│                    Execution Trace                           │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              SuperController (Diagnosis)                 ││
│  │   Classify failure: PROMPT | TOOL | RETRIEVAL | MEMORY  ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         ↓                 ↓                 ↓               │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│   │SuperPrompt│     │SuperReflexion│  │ SuperRAG │           │
│   │(Prompts) │     │  (Tools)  │     │(Retrieval)│           │
│   └──────────┘     └──────────┘     └──────────┘           │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ↓                                  │
│              Natural Language Gradient (∇_NL)               │
│                           ↓                                  │
│                  Updated Environment Φ                       │
└─────────────────────────────────────────────────────────────┘
```

**Optimization Steps:**

1. **Execute**: Run agent task under current environment
2. **Capture**: Record structured execution trace
3. **Diagnose**: SuperController classifies the failure mode
4. **Route**: Send trace to the appropriate optimizer
5. **Generate**: Create Natural Language Gradient update
6. **Validate**: Check update against stability constraints
7. **Apply**: Update environment and persist
8. **Repeat**: Continue until convergence

## Components

### SuperController

Diagnostic meta-controller that classifies failures into:
- **PROMPT**: Instruction violations, format errors
- **TOOL**: Schema violations, invalid arguments
- **RETRIEVAL**: Missing symbols, empty results
- **MEMORY**: Repeated mistakes, contradictions

### SuperPrompt

Evolutionary prompt optimizer using:
- Reflective mutation guided by execution traces
- Pareto-based selection across multiple objectives
- Population-based search

### SuperReflexion

Tool schema repair that:
- Analyzes tool failures
- Generates schema clarifications
- Appends constraints to tool descriptions

### SuperRAG

Retrieval optimizer that adapts:
- `top_k` retrieval count
- Chunk size and overlap
- Reranking thresholds
- Semantic vs structural modes

### SuperMem

Typed memory system with:
- Type hierarchy (TOOL_RULE > RAG_HEURISTIC > STRATEGY)
- Exponential decay
- Conflict resolution
- Confidence tracking

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

## Running Evaluations

### Evaluate on Sample Tasks

```bash
# Run baseline (no optimization)
python scripts/evaluate_baseline.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/baseline.json

# Run with GEPA (prompt-only optimization)
python scripts/evaluate_gepa.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/gepa.json

# Run with SuperOpt (full optimization)
python scripts/evaluate_superopt.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/superopt.json

# Compare all methods
python scripts/compare_all.py \
    --tasks data/tasks/sample_tasks.json \
    --output results/comparison.json
```

### Analyze Results

```bash
python scripts/analyze_results.py --results-dir results/
```

## Project Structure

```
superopt/
├── superopt/                 # Main package
│   ├── core/                 # Core abstractions
│   │   ├── environment.py    # AgenticEnvironment, PromptConfig, ToolSchema
│   │   ├── trace.py          # ExecutionTrace, ToolCall
│   │   └── nlg.py            # NaturalLanguageGradient
│   ├── adapters/             # Agent framework integrations
│   │   ├── base.py           # AgentAdapter base class
│   │   ├── aider_adapter.py  # Aider integration
│   │   └── letta_adapter.py  # Letta integration
│   ├── comparison/           # Comparison with baselines
│   ├── rag/                  # RAG optimization (LanceDB)
│   ├── optimizer.py          # Main SuperOpt class
│   ├── supercontroller.py    # Failure diagnosis
│   ├── superprompt.py        # Prompt optimization
│   ├── superreflexion.py     # Tool schema repair
│   ├── superrag.py           # Retrieval optimization
│   └── supermem.py           # Memory optimization
├── examples/                 # Usage examples
├── scripts/                  # Evaluation scripts
├── data/                     # Task datasets
├── tests/                    # Unit tests
└── pyproject.toml            # Package configuration
```

## Evaluation

SuperOpt evaluates improvements along multiple dimensions:

- **Reliability**: Reduction in repeated failures
- **Stability**: Persistence of improvements over time
- **Efficiency**: Token usage, retry counts
- **Generalization**: Transfer across tasks
- **Interpretability**: Human-readable updates

## Paper

This implementation accompanies the paper:

> **SuperOpt: Agentic Environment Optimization for Autonomous AI Agents**
> Shashi Jagtap, Superagentic AI
> arXiv:XXXX.XXXXX (2025)

## Related Work

SuperOpt builds on and extends:
- **GEPA** [Agrawal et al., 2025]: Evolutionary prompt optimization
- **ACE** [Zhang et al., 2025]: Agentic context engineering
- **Meta-ACE** [Romero, 2025]: Meta-reasoning extensions
- **DSPy** [Khattab et al., 2023]: Prompt programming framework
- **TextGrad** [Yuksekgonul et al., 2024]: Textual differentiation

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/SuperagenticAI/superopt.git
cd superopt
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .

# Type checking
mypy superopt/
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Citation

If you use SuperOpt in your research, please cite:

```bibtex
@misc{jagtap2025superopt,
  title={SuperOpt: Agentic Environment Optimization for Autonomous AI Agents},
  author={Jagtap, Shashi},
  year={2025},
  howpublished={\url{https://github.com/SuperagenticAI/superopt}},
  note={Superagentic AI}
}
```

## Support

- **Issues**: [GitHub Issues](https://github.com/SuperagenticAI/superopt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SuperagenticAI/superopt/discussions)
- **Email**: shashi@super-agentic.ai

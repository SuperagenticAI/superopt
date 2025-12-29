# System Architecture

SuperOpt works as an outer optimization loop around normal agent execution.

## Core Components

### SuperController
- Diagnoses what went wrong
- Routes problems to right optimizer
- Tracks failure patterns

### Optimization Engines
- **SuperPrompt**: Fixes instructions and prompts
- **SuperReflexion**: Repairs tool schemas
- **SuperRAG**: Optimizes information retrieval
- **SuperMem**: Manages learned knowledge

### Environment
- **Prompts**: Instructions for agent behavior
- **Tools**: Functions and commands available
- **Retrieval**: Information search settings
- **Memory**: Learned rules and patterns

## How It Works

```
Agent Task → Agent Execution → Results
    ↑                                ↓
    └────── SuperOpt Analysis ──────┘
           (Learn & Improve)
```

## Integration

SuperOpt integrates with agents through adapters:

- **AiderAdapter**: Connects to Aider coding assistant
- **LettaAdapter**: Connects to Letta memory agents
- **CodexAdapter**: Connects to Codex code generation
- **CustomAdapter**: For other agent frameworks

## Data Flow

1. Agent executes task
2. Execution trace captured
3. SuperController diagnoses failure type
4. Routes to appropriate optimization engine
5. Engine generates environment updates
6. Environment applied back to agent
7. Agent improves over time
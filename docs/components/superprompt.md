# 📝 SuperPrompt

SuperPrompt is the evolutionary instruction optimizer in SuperOpt. It improves system prompts, instructions, and examples using evolutionary search techniques.

## 🎯 Core Function

SuperPrompt optimizes the prompt configuration when agents fail due to instruction-related issues:

- Unclear or incomplete instructions
- Missing examples for edge cases
- Output format requirements not followed
- Behavioral constraints not properly defined

## 🔄 Evolutionary Optimization Process

### Population-Based Search
SuperPrompt maintains a population of candidate prompt configurations:

```python
class PromptCandidate:
    def __init__(self, prompt: PromptConfig, scores: dict[str, float]):
        self.prompt = prompt        # The prompt configuration
        self.scores = scores        # Performance scores on objectives
```

### Multi-Objective Optimization
Uses Pareto dominance to balance multiple goals:

```python
def dominates(self, other: PromptCandidate) -> bool:
    """
    A candidate dominates if it's better or equal in all objectives
    and strictly better in at least one.
    """
    better_in_any = False
    for metric in self.scores:
        if self.scores[metric] < other.scores[metric]:
            return False  # Worse in at least one metric
        if self.scores[metric] > other.scores[metric]:
            better_in_any = True
    return better_in_any
```

## 🎯 Optimization Objectives

### Primary Objectives
- **Task Success Rate**: Percentage of tasks completed successfully
- **Instruction Compliance**: How well agent follows given instructions
- **Output Quality**: Accuracy and relevance of responses
- **Format Adherence**: Following specified output formats

### Secondary Objectives
- **Token Efficiency**: Reducing unnecessary token usage
- **Response Speed**: Minimizing processing time
- **Error Reduction**: Decreasing specific failure types

## 🔧 Prompt Evolution Strategies

### Mutation Operations
- **Instruction Enhancement**: Add clarifying details to system prompts
- **Example Addition**: Include new few-shot examples
- **Constraint Addition**: Add behavioral constraints
- **Format Specification**: Clarify output format requirements

### Crossover Operations
- **Instruction Combination**: Merge effective instructions from different candidates
- **Example Pooling**: Combine examples from successful candidates
- **Constraint Merging**: Combine complementary constraints

### Selection Mechanisms
- **Tournament Selection**: Select best candidates for reproduction
- **Pareto Front Selection**: Prefer non-dominated solutions
- **Diversity Preservation**: Maintain population diversity

## 📊 Population Management

### Population Size
- **Default**: 10-20 candidates
- **Scalable**: Can handle larger populations for complex optimization

### Generation Limits
- **Maximum Generations**: Prevent excessive computation
- **Convergence Criteria**: Stop when improvement stalls
- **Time Limits**: Respect computational budgets

## 🎨 Prompt Configuration Structure

SuperPrompt optimizes all aspects of the prompt environment:

```python
@dataclass
class PromptConfig:
    system_prompt: str                    # Main system instructions
    instruction_policy: str              # Specific behavior rules
    few_shot_exemplars: list[str]        # Example interactions
    output_format_spec: str              # Required output formats
    behavioral_constraints: list[str]    # Rules and limitations
```

## 🔄 Integration with SuperOpt

### Trigger Conditions
SuperPrompt activates when SuperController diagnoses:
- `FailureType.PROMPT` failures
- Instruction violations
- Output format errors
- Reasoning hallucinations

### Input Processing
```python
# SuperPrompt receives execution traces with prompt failures
def optimize(self, trace: ExecutionTrace, environment: AgenticEnvironment):
    # Extract prompt-related failure information
    # Generate improved prompt candidates
    # Evaluate candidates through agent execution
    # Return best performing prompt configuration
```

### Output Generation
Returns updated `PromptConfig` with:
- Enhanced system instructions
- Additional examples
- New behavioral constraints
- Improved format specifications

## ⚙️ Configuration Options

### Basic Configuration
```python
superprompt = SuperPrompt(
    population_size=10,      # Number of candidate prompts
    max_generations=5,       # Evolution iterations
    mutation_rate=0.3,       # Probability of mutations
)
```

### Advanced Configuration
```python
superprompt = SuperPrompt(
    population_size=20,
    max_generations=10,
    mutation_rate=0.4,
    crossover_rate=0.7,
    tournament_size=3,
    objectives=['success_rate', 'token_efficiency', 'format_compliance']
)
```

## 🔬 Research Foundation

SuperPrompt builds on **GEPA (Generative Evolutionary Prompt Optimization)** principles:

- **Evolutionary Search**: Population-based optimization
- **Pareto Objectives**: Multi-objective balancing
- **Generative Updates**: Natural language prompt improvements

However, SuperPrompt integrates these techniques into the broader SuperOpt framework, coordinating with other optimizers for comprehensive environment improvement.

## 📈 Performance Characteristics

### Strengths
- **Creative Improvements**: Can generate novel prompt structures
- **Multi-Objective**: Balances competing requirements
- **Adaptive**: Learns from diverse failure patterns

### Limitations
- **Computationally Intensive**: Requires multiple evaluation cycles
- **Domain Dependent**: Effectiveness varies by task type
- **Evaluation Overhead**: Needs agent execution to score candidates

SuperPrompt provides the intelligent prompt optimization that makes SuperOpt's comprehensive approach possible.
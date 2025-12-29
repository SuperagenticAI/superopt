# 🧠 SuperMem

SuperMem is the typed memory system in SuperOpt that manages learned patterns, rules, and heuristics. It prevents memory from becoming contradictory, stale, or overly generic through structure, typing, and decay mechanisms.

## 🎯 Core Function

SuperMem addresses memory-related failures:

- Agents repeat mistakes they've made before
- Learned patterns conflict with current tasks
- Knowledge becomes outdated or incorrect
- Important context gets forgotten

## 🏗️ Memory Architecture

### Typed Memory Entries
SuperMem organizes memory into typed categories:

```python
@dataclass
class MemoryEntry:
    entry_type: str              # Memory category
    content: str                 # The learned information
    confidence: float           # How reliable this knowledge is
    timestamp: datetime         # When this was learned
    helpful_count: int          # How many times this helped
    harmful_count: int          # How many times this caused problems
```

### Memory Types Hierarchy
```python
TYPE_HIERARCHY = {
    "TOOL_RULE": 4,           # Highest priority - tool usage rules
    "SAFETY_CONSTRAINT": 4,   # Safety and security rules
    "RAG_HEURISTIC": 3,       # Retrieval optimization hints
    "PROMPT_CONSTRAINT": 2,   # Prompt behavior rules
    "STRATEGY": 1,            # General problem-solving approaches
    "STYLE_GUIDELINE": 1,     # Output formatting preferences
}
```

Higher priority types override lower priority types when conflicts occur.

## ⏰ Memory Decay System

### Exponential Decay
Memory entries lose confidence over time to prevent stale knowledge:

```python
def decay(self, lambda_decay: float, current_time: datetime) -> float:
    """Apply exponential decay to confidence."""
    total_seconds = (current_time - self.timestamp).total_seconds()
    delta_t = total_seconds / 3600  # hours
    decay_factor = (1.0 - lambda_decay) ** delta_t
    return self.confidence * decay_factor
```

### Type-Specific Decay Rates
Different memory types decay at different rates:
```python
DECAY_CONSTANTS = {
    "TOOL_RULE": 0.01,        # Very slow decay (long-term rules)
    "SAFETY_CONSTRAINT": 0.01, # Critical rules persist
    "RAG_HEURISTIC": 0.05,    # Moderate decay
    "PROMPT_CONSTRAINT": 0.1, # Faster decay for behavior rules
    "STRATEGY": 0.15,         # General strategies decay faster
    "STYLE_GUIDELINE": 0.2,   # Preferences decay quickly
}
```

## ⚖️ Conflict Resolution

### Hierarchy-Based Resolution
When memory entries conflict, higher-priority types win:
```python
def resolve_conflicts(self, memory: list[MemoryEntry]) -> list[MemoryEntry]:
    """Resolve conflicts using type hierarchy."""
    # Group by content similarity
    # For conflicts, keep highest priority type
    # Merge confidence scores appropriately
```

### Confidence-Based Filtering
Low-confidence memories are filtered out:
```python
def filter_by_confidence(self, memory: list[MemoryEntry],
                        threshold: float) -> list[MemoryEntry]:
    """Remove memories below confidence threshold."""
    return [entry for entry in memory
            if entry.confidence >= threshold]
```

## 🔄 Memory Dynamics

### Learning New Patterns
When agents succeed or encounter patterns, SuperMem learns:
```python
def learn_pattern(self, trace: ExecutionTrace,
                 environment: AgenticEnvironment) -> list[MemoryEntry]:
    # Extract successful strategies
    # Identify helpful patterns
    # Create new memory entries
    # Set appropriate confidence scores
```

### Updating Existing Knowledge
```python
def update_confidence(self, memory: list[MemoryEntry],
                     trace: ExecutionTrace) -> list[MemoryEntry]:
    # Find relevant existing memories
    # Increase helpful_count for successful memories
    # Increase harmful_count for problematic memories
    # Adjust confidence scores accordingly
```

### Maintenance Operations
Regular cleanup prevents memory bloat:
```python
def maintenance(self, memory: list[MemoryEntry]) -> list[MemoryEntry]:
    # Apply decay to all entries
    # Remove low-confidence entries
    # Resolve conflicts
    # Consolidate similar entries
    return cleaned_memory
```

## 🔄 Integration with SuperOpt

### Trigger Conditions
SuperMem activates for `FailureType.MEMORY` diagnoses:
- Repeated mistakes despite previous learning
- Conflicts with established patterns
- Outdated knowledge causing failures
- Missing context from forgotten information

### Memory Updates
```python
# SuperMem receives memory-related failures
def optimize(self, trace: ExecutionTrace, environment: AgenticEnvironment):
    # Analyze memory conflicts and gaps
    # Generate new memory entries
    # Update confidence scores
    # Apply conflict resolution
    # Return updated memory list
```

### Environment Integration
Memory becomes part of the agent environment:
```python
# Memory integrates with agent execution
environment = AgenticEnvironment(
    prompts=prompt_config,
    tools=tool_schemas,
    retrieval=retrieval_config,
    memory=memory_entries    # SuperMem managed entries
)
```

## ⚙️ Configuration Options

### Basic Configuration
```python
supermem = SuperMem(
    min_confidence=0.1,      # Minimum confidence threshold
)
```

### Advanced Configuration
```python
supermem = SuperMem(
    min_confidence=0.2,
    max_memory_entries=1000,    # Memory capacity limit
    decay_interval_hours=24,    # How often to apply decay
    conflict_resolution=True,   # Enable conflict resolution
    consolidation_threshold=0.8 # Similarity threshold for consolidation
)
```

## 📊 Memory Health Metrics

### Quality Indicators
- **Confidence Distribution**: How reliable memories are
- **Type Balance**: Distribution across memory types
- **Conflict Frequency**: How often resolutions are needed
- **Helpful/Harmful Ratio**: Success rate of memory application

### Performance Monitoring
- **Memory Size**: Number of active entries
- **Decay Rate**: How quickly memories lose relevance
- **Learning Rate**: How fast new patterns are acquired
- **Retrieval Speed**: How quickly relevant memories are found

## 🔬 Research Foundation

SuperMem implements **structured memory management**:

- **Type System**: Prevents memory pollution with categorization
- **Decay Mechanisms**: Ensures freshness and relevance
- **Conflict Resolution**: Maintains consistency across memories
- **Confidence Tracking**: Enables quality-based filtering

Unlike simple memory buffers, SuperMem provides the structured memory system that enables reliable long-term learning and prevents catastrophic forgetting.

## 📈 Effectiveness Characteristics

### Memory Quality
- **Relevance**: Memories stay current and applicable
- **Consistency**: No conflicting information
- **Completeness**: Covers all learned patterns
- **Efficiency**: Fast retrieval without overhead

### Learning Dynamics
- **Accumulation**: Builds knowledge over time
- **Adaptation**: Updates based on new experiences
- **Stabilization**: Prevents oscillation and instability
- **Generalization**: Applies patterns across similar situations

SuperMem provides the intelligent memory management that enables SuperOpt's continuous learning capabilities by maintaining reliable, conflict-free knowledge that improves over time.

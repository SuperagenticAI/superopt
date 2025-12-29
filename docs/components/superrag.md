# 🔍 SuperRAG

SuperRAG is the adaptive retrieval optimization engine in SuperOpt. It treats the retrieval configuration as a tunable control surface, adapting parameters based on execution trace feedback to improve information access.

## 🎯 Core Function

SuperRAG optimizes how agents find and access information when retrieval failures occur:

- Agents can't find relevant information
- Search results are empty or irrelevant
- Context windows overflow or are insufficient
- Retrieved information contains hallucinations

## 🔧 Retrieval Parameters

SuperRAG tunes multiple aspects of the retrieval pipeline:

```python
@dataclass
class RetrievalConfig:
    top_k: int = 5                    # Number of documents to retrieve
    chunk_size: int = 512             # Size of text chunks
    chunk_overlap: int = 50           # Overlap between chunks
    rerank_threshold: float = 0.7     # Relevance threshold for reranking
    mode: str = "semantic"            # "semantic" or "structural"
    query_rewrite_strategy: str = "default"
    file_type_filters: list[str] = [] # Restrict to file types
    dependency_expansion_depth: int = 1
```

## 📊 Failure Pattern Analysis

### Missing Information Failures
**Symptoms**: Agent can't find symbols, files, or concepts
**Causes**: Too few results, wrong retrieval mode
**Solutions**:
- Increase `top_k` to retrieve more documents
- Switch from `semantic` to `structural` mode
- Add broader file type filters

### Context Quality Issues
**Symptoms**: Retrieved information is noisy or irrelevant
**Causes**: Poor chunking, low relevance thresholds
**Solutions**:
- Reduce `chunk_size` for more precise chunks
- Increase `rerank_threshold` for stricter relevance
- Adjust `chunk_overlap` for better continuity

### Context Overflow Problems
**Symptoms**: Too much information, context window limits exceeded
**Causes**: Over-retrieval, large chunks
**Solutions**:
- Decrease `top_k` to limit results
- Reduce `chunk_size` for smaller pieces
- Optimize `query_rewrite_strategy`

## 🔄 Adaptive Tuning Process

### Parameter Adjustment Logic
```python
def tune(self, config: RetrievalConfig, trace: ExecutionTrace) -> RetrievalConfig:
    # Analyze failure patterns
    if trace.missing_symbol():
        # Increase retrieval breadth
        config.top_k = min(config.top_k + 2, self.max_top_k)
        config.mode = "structural"

    elif trace.retrieval_noisy():
        # Improve relevance filtering
        config.chunk_size = max(config.chunk_size - 50, 256)
        config.rerank_threshold += 0.1

    elif trace.context_overflow():
        # Reduce information volume
        config.top_k = max(config.top_k - 1, self.min_top_k)
        config.chunk_size = max(config.chunk_size - 100, 128)
```

### Bounds Checking
SuperRAG respects parameter limits:
- `top_k` stays within `min_top_k` to `max_top_k` range
- `chunk_size` maintains minimum effective size
- `rerank_threshold` stays within 0.0 to 1.0

## 🎯 Optimization Strategies

### Semantic vs Structural Retrieval
- **Semantic**: Uses meaning and similarity for broad discovery
- **Structural**: Uses code structure for precise symbol lookup
- **Adaptive Switching**: Changes mode based on failure patterns

### Query Enhancement
- **Rewrite Strategies**: Rephrase queries for better results
- **Expansion Techniques**: Add related terms and synonyms
- **Context Incorporation**: Include task context in queries

### Chunking Optimization
- **Size Adjustment**: Balance precision vs completeness
- **Overlap Tuning**: Ensure continuity without redundancy
- **Content-Aware**: Consider code vs text boundaries

## 🔄 Integration with SuperOpt

### Trigger Conditions
SuperRAG activates for `FailureType.RETRIEVAL` diagnoses:
- Missing symbol errors
- Empty retrieval results
- Context overflow issues
- Relevance quality problems

### Feedback Loop
```python
# SuperRAG receives retrieval failures
def optimize(self, trace: ExecutionTrace, environment: AgenticEnvironment):
    # Analyze retrieval performance
    # Identify parameter adjustments needed
    # Tune retrieval configuration
    # Return updated RetrievalConfig
```

### Environment Updates
Changes are applied to the retrieval environment:
```python
# Before optimization
retrieval = RetrievalConfig(
    top_k=3,
    chunk_size=512,
    mode="semantic"
)

# After SuperRAG tuning
retrieval = RetrievalConfig(
    top_k=5,           # Increased for broader search
    chunk_size=512,    # Maintained
    mode="structural"  # Switched for better symbol finding
)
```

## ⚙️ Configuration Options

### Basic Configuration
```python
superrag = SuperRAG(
    max_top_k=50,      # Maximum retrieval count
    min_top_k=1        # Minimum retrieval count
)
```

### Advanced Configuration
```python
superrag = SuperRAG(
    max_top_k=100,
    min_top_k=1,
    adaptation_rate=0.2,           # How aggressively to adjust parameters
    feedback_window=10,             # Number of traces to consider
    enable_query_rewriting=True,    # Allow query modifications
    mode_switching=True             # Allow semantic/structural switching
)
```

## 📊 Performance Monitoring

### Success Metrics
- **Retrieval Coverage**: Percentage of queries that find relevant information
- **Relevance Quality**: How well retrieved documents match needs
- **Context Efficiency**: Optimal use of context windows

### Adaptation Tracking
- **Parameter History**: Track how parameters change over time
- **Effectiveness Scoring**: Measure impact of each adjustment
- **Stability Analysis**: Ensure changes don't cause oscillations

## 🔬 Research Foundation

SuperRAG implements **adaptive retrieval optimization**:

- **Parameter Tuning**: Treats retrieval as a control system
- **Failure-Driven Adaptation**: Uses execution feedback for improvement
- **Multi-Parameter Optimization**: Coordinates multiple retrieval aspects

Unlike static retrieval configurations, SuperRAG continuously adapts based on actual agent performance, creating retrieval systems that improve over time.

## 📈 Effectiveness Characteristics

### Strengths
- **Immediate Impact**: Parameter changes take effect immediately
- **Broad Applicability**: Works across different retrieval systems
- **Data-Driven**: Based on actual failure patterns

### Optimization Scope
- **Query Processing**: How searches are formulated
- **Result Ranking**: How documents are scored and ordered
- **Context Management**: How information is chunked and presented
- **System Integration**: How retrieval connects to agent reasoning

SuperRAG provides the intelligent retrieval optimization that ensures agents can always find the information they need.
"""
SuperRAG: Adaptive Retrieval Optimization

SuperRAG treats retrieval configuration as a tunable control surface,
adapting parameters based on execution trace feedback.
"""

from superopt.core.environment import AgenticEnvironment, RetrievalConfig
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace


class SuperRAG:
    """
    Retrieval optimization engine.

    SuperRAG adapts retrieval parameters based on failure patterns:
    - Missing symbols: Increase top_k, switch to structural retrieval
    - Noisy context: Reduce chunk_size, increase rerank_threshold
    - Context overflow: Reduce top_k, optimize chunking
    """

    def __init__(self, max_top_k: int = 50, min_top_k: int = 1):
        """
        Initialize SuperRAG.

        Args:
            max_top_k: Maximum allowed top_k value
            min_top_k: Minimum allowed top_k value
        """
        self.max_top_k = max_top_k
        self.min_top_k = min_top_k
        self.adaptation_history: list = []

    def tune(self, config: RetrievalConfig, trace: ExecutionTrace) -> RetrievalConfig:
        """
        Tune retrieval configuration based on execution trace.

        Args:
            config: Current retrieval configuration
            trace: Execution trace with retrieval feedback

        Returns:
            Updated retrieval configuration
        """
        new_config = RetrievalConfig(
            top_k=config.top_k,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            rerank_threshold=config.rerank_threshold,
            mode=config.mode,
            query_rewrite_strategy=config.query_rewrite_strategy,
            file_type_filters=config.file_type_filters.copy(),
            dependency_expansion_depth=config.dependency_expansion_depth,
        )

        # Adapt based on failure patterns
        if trace.missing_symbol():
            # Increase retrieval breadth
            new_config.top_k = min(config.top_k + 5, self.max_top_k)
            new_config.mode = "structural"  # Switch to structural for symbol lookup
            new_config.dependency_expansion_depth = min(config.dependency_expansion_depth + 1, 3)

        if trace.noisy_context():
            # Reduce noise
            new_config.rerank_threshold = min(config.rerank_threshold + 0.1, 0.95)
            new_config.chunk_size = max(config.chunk_size - 100, 256)
            if new_config.top_k > 3:
                new_config.top_k = max(config.top_k - 2, self.min_top_k)

        if trace.retrieval_empty():
            # Increase retrieval when empty
            new_config.top_k = min(config.top_k + 3, self.max_top_k)
            new_config.mode = "semantic"  # Try semantic if structural failed

        # Check for context overflow (heuristic: many large retrievals)
        if len(trace.retrieval_queries) > 5:
            total_retrieved = sum(len(q.retrieved_documents) for q in trace.retrieval_queries)
            if total_retrieved > 50:  # Threshold for overflow
                new_config.top_k = max(config.top_k - 3, self.min_top_k)
                new_config.chunk_size = max(config.chunk_size - 50, 256)

        # Record adaptation
        self.adaptation_history.append(
            {
                "trace_id": trace.task_id,
                "changes": {
                    "top_k": (config.top_k, new_config.top_k),
                    "mode": (config.mode, new_config.mode),
                    "rerank_threshold": (config.rerank_threshold, new_config.rerank_threshold),
                },
            }
        )

        return new_config

    def adapt(
        self, environment: AgenticEnvironment, trace: ExecutionTrace
    ) -> NaturalLanguageGradient:
        """
        Adapt retrieval configuration based on execution trace.

        Args:
            environment: Current environment
            trace: Execution trace with retrieval feedback

        Returns:
            Natural Language Gradient with retrieval updates
        """
        tuned_config = self.tune(environment.retrieval, trace)

        # Compute delta
        delta_r = {}
        if tuned_config.top_k != environment.retrieval.top_k:
            delta_r["top_k"] = tuned_config.top_k
        if tuned_config.mode != environment.retrieval.mode:
            delta_r["mode"] = tuned_config.mode
        if tuned_config.rerank_threshold != environment.retrieval.rerank_threshold:
            delta_r["rerank_threshold"] = tuned_config.rerank_threshold
        if tuned_config.chunk_size != environment.retrieval.chunk_size:
            delta_r["chunk_size"] = tuned_config.chunk_size
        if (
            tuned_config.dependency_expansion_depth
            != environment.retrieval.dependency_expansion_depth
        ):
            delta_r["dependency_expansion_depth"] = tuned_config.dependency_expansion_depth

        return NaturalLanguageGradient(
            delta_r=delta_r if delta_r else None,
            source_trace_id=trace.task_id,
        )

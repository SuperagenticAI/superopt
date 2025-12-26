"""
SuperMem: Memory, Stability, and Long-Term Control

SuperMem introduces structure, typing, and decay to prevent memory
from becoming contradictory, stale, or overly generic.
"""

from datetime import datetime

from superopt.core.environment import AgenticEnvironment, MemoryEntry
from superopt.core.nlg import NaturalLanguageGradient
from superopt.core.trace import ExecutionTrace


class SuperMem:
    """
    Typed memory system with decay and conflict resolution.

    Memory entries are:
    - Typed (STRATEGY, TOOL_RULE, RAG_HEURISTIC, PROMPT_CONSTRAINT)
    - Timestamped with confidence scores
    - Subject to exponential decay
    - Resolved for conflicts via hierarchy
    """

    # Memory type hierarchy (higher priority overrides lower)
    TYPE_HIERARCHY = {
        "TOOL_RULE": 4,
        "SAFETY_CONSTRAINT": 4,
        "RAG_HEURISTIC": 3,
        "PROMPT_CONSTRAINT": 2,
        "STRATEGY": 1,
        "STYLE_GUIDELINE": 1,
    }

    # Decay constants per type (lambda values)
    DECAY_CONSTANTS = {
        "TOOL_RULE": 0.01,  # Very slow decay
        "SAFETY_CONSTRAINT": 0.01,
        "RAG_HEURISTIC": 0.05,
        "PROMPT_CONSTRAINT": 0.1,
        "STRATEGY": 0.15,
        "STYLE_GUIDELINE": 0.2,
    }

    def __init__(self, min_confidence: float = 0.1):
        """
        Initialize SuperMem.

        Args:
            min_confidence: Minimum confidence threshold for keeping entries
        """
        self.min_confidence = min_confidence

    def ingest(self, memory: list[MemoryEntry], trace: ExecutionTrace) -> list[MemoryEntry]:
        """
        Ingest new memory entries from execution trace.

        Args:
            memory: Current memory entries
            trace: Execution trace to extract rules from

        Returns:
            Updated memory list with new entries and conflicts resolved
        """
        # Extract rules from trace
        new_entries = self._extract_rules(trace)

        # Resolve conflicts
        updated_memory = memory.copy()
        for entry in new_entries:
            updated_memory = self._resolve_conflict(entry, updated_memory)

        # Apply decay
        updated_memory = self._decay(updated_memory)

        # Prune low-confidence entries
        updated_memory = [
            entry for entry in updated_memory if entry.confidence >= self.min_confidence
        ]

        return updated_memory

    def update(
        self, environment: AgenticEnvironment, trace: ExecutionTrace
    ) -> NaturalLanguageGradient:
        """
        Update memory based on execution trace.

        Args:
            environment: Current environment
            trace: Execution trace

        Returns:
            Natural Language Gradient with memory updates
        """
        updated_memory = self.ingest(environment.memory, trace)

        # Compute delta (new entries)
        existing_ids = {id(e) for e in environment.memory}
        new_entries = [entry for entry in updated_memory if id(entry) not in existing_ids]

        return NaturalLanguageGradient(
            delta_m=new_entries if new_entries else None,
            source_trace_id=trace.task_id,
        )

    def _extract_rules(self, trace: ExecutionTrace) -> list[MemoryEntry]:
        """
        Extract memory entries from execution trace.

        Returns:
            List of new memory entries
        """
        entries = []

        # Extract tool rules from tool errors
        for error in trace.tool_errors:
            if error.error_message:
                entry = MemoryEntry(
                    entry_type="TOOL_RULE",
                    content=f"When using {error.tool_name}: {error.error_message}",
                    confidence=0.8,
                    helpful_count=1,
                )
                entries.append(entry)

        # Extract retrieval heuristics from retrieval failures
        if trace.missing_symbol():
            entry = MemoryEntry(
                entry_type="RAG_HEURISTIC",
                content="When symbols are missing, increase top_k and use structural retrieval",
                confidence=0.7,
                helpful_count=1,
            )
            entries.append(entry)

        # Extract strategies from successful patterns
        if trace.success and trace.tool_calls:
            # Could extract successful patterns here
            pass

        return entries

    def _resolve_conflict(
        self, new_entry: MemoryEntry, memory: list[MemoryEntry]
    ) -> list[MemoryEntry]:
        """
        Resolve conflicts between new entry and existing memory.

        Uses hierarchy of mutability to determine which entry takes precedence.
        """
        new_priority = self.TYPE_HIERARCHY.get(new_entry.entry_type, 0)

        # Check for conflicts
        conflicting_indices = []
        for i, existing_entry in enumerate(memory):
            if self._conflicts(new_entry, existing_entry):
                existing_priority = self.TYPE_HIERARCHY.get(existing_entry.entry_type, 0)

                if new_priority > existing_priority:
                    # New entry overrides
                    conflicting_indices.append(i)
                elif new_priority == existing_priority:
                    # Same priority: compare confidence
                    if new_entry.confidence > existing_entry.confidence:
                        conflicting_indices.append(i)
                    else:
                        # Existing entry wins, don't add new entry
                        return memory

        # Remove conflicting entries
        updated_memory = [entry for i, entry in enumerate(memory) if i not in conflicting_indices]

        # Add new entry
        updated_memory.append(new_entry)

        return updated_memory

    def _conflicts(self, entry1: MemoryEntry, entry2: MemoryEntry) -> bool:
        """
        Check if two memory entries conflict.

        Simple semantic similarity check - can be enhanced with embeddings.
        """
        # Simple heuristic: check if content is very similar
        content1 = entry1.content.lower()
        content2 = entry2.content.lower()

        # Check for direct contradiction keywords
        contradiction_pairs = [
            ("always", "never"),
            ("must", "must not"),
            ("required", "forbidden"),
            ("use", "avoid"),
        ]

        for word1, word2 in contradiction_pairs:
            if (word1 in content1 and word2 in content2) or (
                word2 in content1 and word1 in content2
            ):
                # Check if they're about the same topic
                if self._similar_topic(content1, content2):
                    return True

        return False

    def _similar_topic(self, content1: str, content2: str) -> bool:
        """Check if two memory entries are about similar topics."""
        # Extract key terms (simple word-based approach)
        words1 = set(content1.split())
        words2 = set(content2.split())

        # Check for significant overlap
        overlap = len(words1 & words2)
        total_unique = len(words1 | words2)

        if total_unique == 0:
            return False

        similarity = overlap / total_unique
        return similarity > 0.3  # Threshold

    def _decay(self, memory: list[MemoryEntry]) -> list[MemoryEntry]:
        """
        Apply exponential decay to memory entries.

        C(t) = C0 * (1 - lambda)^(delta_t)
        """
        current_time = datetime.now()
        decayed_memory = []

        for entry in memory:
            lambda_decay = self.DECAY_CONSTANTS.get(entry.entry_type, 0.1)
            new_confidence = entry.decay(lambda_decay, current_time)

            # Create updated entry
            updated_entry = MemoryEntry(
                entry_type=entry.entry_type,
                content=entry.content,
                confidence=new_confidence,
                timestamp=entry.timestamp,
                helpful_count=entry.helpful_count,
                harmful_count=entry.harmful_count,
            )
            decayed_memory.append(updated_entry)

        return decayed_memory

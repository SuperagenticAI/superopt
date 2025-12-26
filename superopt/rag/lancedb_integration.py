"""
LanceDB Integration for SuperRAG

Integrates LanceDB vector database with SuperRAG for adaptive
retrieval optimization. LanceDB provides fast vector search
capabilities for code retrieval.
"""

from typing import Any

from superopt.core.environment import RetrievalConfig
from superopt.core.trace import RetrievalQuery


class LanceDBRetrievalBackend:
    """
    LanceDB-backed retrieval backend for SuperRAG.

    Provides vector search capabilities for code retrieval
    with adaptive configuration based on SuperOpt feedback.
    """

    def __init__(
        self,
        db_path: str,
        table_name: str = "code_vectors",
        embedding_model: str | None = None,
    ):
        """
        Initialize LanceDB retrieval backend.

        Args:
            db_path: Path to LanceDB database
            table_name: Name of the table for code vectors
            embedding_model: Embedding model name (optional)
        """
        self.db_path = db_path
        self.table_name = table_name
        self.embedding_model = embedding_model
        self._db = None
        self._table = None

    def initialize(self):
        """Initialize LanceDB connection."""
        try:
            import lancedb

            self._db = lancedb.connect(self.db_path)

            # Try to open existing table
            try:
                self._table = self._db.open_table(self.table_name)
            except Exception:
                # Table doesn't exist, will be created on first insert
                self._table = None
        except ImportError:
            raise ImportError(
                "lancedb is required for LanceDB integration. Install with: pip install lancedb"
            )

    def search(
        self,
        query: str,
        config: RetrievalConfig,
    ) -> RetrievalQuery:
        """
        Perform vector search using LanceDB.

        Args:
            query: Search query
            config: Retrieval configuration

        Returns:
            RetrievalQuery with results
        """
        if not self._table:
            # Return empty results if table not initialized
            return RetrievalQuery(
                query=query,
                retrieved_documents=[],
                ranking_scores=[],
            )

        try:
            # Perform vector search
            results = self._table.search(query).limit(config.top_k).to_pandas()

            # Extract documents and scores
            documents = []
            scores = []

            for _, row in results.iterrows():
                documents.append(
                    {
                        "content": row.get("text", ""),
                        "metadata": {k: v for k, v in row.items() if k not in ["vector", "text"]},
                    }
                )
                # Extract similarity score if available
                score = row.get("_distance", 1.0)  # Lower is better for distance
                scores.append(1.0 - min(score, 1.0))  # Convert to similarity

            return RetrievalQuery(
                query=query,
                retrieved_documents=documents,
                ranking_scores=scores,
            )
        except Exception:
            # Return empty on error
            return RetrievalQuery(
                query=query,
                retrieved_documents=[],
                ranking_scores=[],
            )

    def index_code(
        self,
        code_chunks: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ):
        """
        Index code chunks in LanceDB.

        Args:
            code_chunks: List of code chunks with text and embeddings
            metadata: Optional metadata to attach
        """
        if not self._db:
            self.initialize()

        if not code_chunks:
            return

        try:
            import pandas as pd

            # Prepare data for insertion
            data = []
            for chunk in code_chunks:
                row = {
                    "text": chunk.get("text", ""),
                    "vector": chunk.get("embedding", []),
                }
                if metadata:
                    row.update(metadata)
                if "metadata" in chunk:
                    row.update(chunk["metadata"])
                data.append(row)

            df = pd.DataFrame(data)

            # Create table if it doesn't exist
            if not self._table:
                self._table = self._db.create_table(
                    self.table_name,
                    df,
                    mode="overwrite",
                )
            else:
                # Append to existing table
                self._table.add(df)
        except Exception as e:
            raise RuntimeError(f"Failed to index code in LanceDB: {e}")

    def update_config(self, config: RetrievalConfig):
        """
        Update retrieval configuration (e.g., create index).

        Args:
            config: Updated retrieval configuration
        """
        if not self._table:
            return

        try:
            # Create vector index if needed
            if config.mode == "semantic":
                # Ensure vector index exists
                # This is a simplified version - actual implementation
                # would check if index exists and create/update as needed
                pass
        except Exception:
            pass

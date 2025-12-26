"""
LanceDB Vector Store for SuperRAG

Provides a configurable vector store for code retrieval that SuperRAG can optimize.
Supports:
- Semantic search (vector)
- Full-text search (keyword)
- Hybrid search (vector + keyword)
- Configurable top_k, reranking, and search modes
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

try:
    import lancedb
    from lancedb.embeddings import get_registry
    from lancedb.pydantic import LanceModel, Vector

    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    LanceModel = object
    Vector = None


@dataclass
class RetrievalConfig:
    """Configuration for retrieval that SuperRAG can optimize."""

    # Core parameters
    top_k: int = 5
    search_mode: Literal["vector", "fts", "hybrid"] = "vector"

    # Hybrid search parameters
    hybrid_weight: float = 0.5  # 0 = all FTS, 1 = all vector

    # Reranking
    use_reranker: bool = False
    reranker_type: Literal["rrf", "linear", "cross_encoder"] = "rrf"

    # Query expansion
    expand_query: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_k": self.top_k,
            "search_mode": self.search_mode,
            "hybrid_weight": self.hybrid_weight,
            "use_reranker": self.use_reranker,
            "reranker_type": self.reranker_type,
            "expand_query": self.expand_query,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetrievalConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CodeChunk:
    """A chunk of code for indexing."""

    file_path: str
    content: str
    chunk_type: Literal["function", "class", "module", "docstring"]
    name: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""

    file_path: str
    content: str
    chunk_type: str
    name: str
    score: float
    start_line: int
    end_line: int


class LanceDBStore:
    """
    LanceDB-based vector store for code retrieval.

    Supports multiple search modes that SuperRAG can optimize:
    - vector: Semantic similarity search
    - fts: Full-text keyword search
    - hybrid: Combination of vector and FTS
    """

    def __init__(
        self,
        db_path: str = "./lancedb_store",
        table_name: str = "code_chunks",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        if not LANCEDB_AVAILABLE:
            raise ImportError(
                "LanceDB not installed. Install with: pip install lancedb sentence-transformers"
            )

        self.db_path = db_path
        self.table_name = table_name
        self.embedding_model = embedding_model

        # Initialize database
        self.db = lancedb.connect(db_path)
        self.table = None
        self._embedding_func = None

    def _get_embedding_func(self):
        """Get or create embedding function."""
        if self._embedding_func is None:
            registry = get_registry()
            self._embedding_func = registry.get("sentence-transformers").create(
                name=self.embedding_model
            )
        return self._embedding_func

    def _create_schema(self):
        """Create the LanceDB table schema."""
        embed_func = self._get_embedding_func()

        class CodeChunkModel(LanceModel):
            text: str = embed_func.SourceField()
            vector: Vector(embed_func.ndims()) = embed_func.VectorField()
            file_path: str
            chunk_type: str
            name: str
            start_line: int
            end_line: int

        return CodeChunkModel

    def index_codebase(self, chunks: list[CodeChunk]) -> int:
        """
        Index code chunks into LanceDB.

        Args:
            chunks: List of code chunks to index

        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0

        # Prepare data for indexing
        data = []
        for chunk in chunks:
            data.append(
                {
                    "text": chunk.content,
                    "file_path": chunk.file_path,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                }
            )

        # Create or overwrite table
        schema = self._create_schema()
        self.table = self.db.create_table(
            self.table_name,
            data=data,
            schema=schema,
            mode="overwrite",
        )

        # Create FTS index for hybrid search
        try:
            self.table.create_fts_index("text", replace=True)
        except Exception:
            pass  # FTS index creation may fail on some platforms

        return len(chunks)

    def search(
        self,
        query: str,
        config: RetrievalConfig | None = None,
    ) -> list[RetrievalResult]:
        """
        Search for code chunks matching the query.

        Args:
            query: Search query
            config: Retrieval configuration (SuperRAG can optimize this)

        Returns:
            List of retrieval results
        """
        if self.table is None:
            # Try to open existing table
            try:
                self.table = self.db.open_table(self.table_name)
            except Exception:
                return []

        config = config or RetrievalConfig()

        try:
            if config.search_mode == "vector":
                results = self._vector_search(query, config)
            elif config.search_mode == "fts":
                results = self._fts_search(query, config)
            elif config.search_mode == "hybrid":
                results = self._hybrid_search(query, config)
            else:
                results = self._vector_search(query, config)
        except Exception:
            # Fallback to vector search on error
            try:
                results = self._vector_search(query, config)
            except Exception:
                return []

        return results

    def _vector_search(
        self,
        query: str,
        config: RetrievalConfig,
    ) -> list[RetrievalResult]:
        """Semantic vector search."""
        results = self.table.search(query).limit(config.top_k).to_pandas()

        return self._parse_results(results)

    def _fts_search(
        self,
        query: str,
        config: RetrievalConfig,
    ) -> list[RetrievalResult]:
        """Full-text keyword search."""
        try:
            results = self.table.search(query, query_type="fts").limit(config.top_k).to_pandas()
        except Exception:
            # FTS may not be available, fall back to vector
            return self._vector_search(query, config)

        return self._parse_results(results)

    def _hybrid_search(
        self,
        query: str,
        config: RetrievalConfig,
    ) -> list[RetrievalResult]:
        """Hybrid search combining vector and FTS."""
        try:
            results = self.table.search(query, query_type="hybrid").limit(config.top_k).to_pandas()
        except Exception:
            # Hybrid may not be available, fall back to vector
            return self._vector_search(query, config)

        return self._parse_results(results)

    def _parse_results(self, df) -> list[RetrievalResult]:
        """Parse pandas DataFrame to RetrievalResult list."""
        results = []
        for _, row in df.iterrows():
            # Get score from _distance or _score column
            score = 1.0
            if "_distance" in row:
                score = 1.0 / (1.0 + float(row["_distance"]))
            elif "_score" in row:
                score = float(row["_score"])

            results.append(
                RetrievalResult(
                    file_path=row["file_path"],
                    content=row["text"],
                    chunk_type=row["chunk_type"],
                    name=row["name"],
                    score=score,
                    start_line=int(row["start_line"]),
                    end_line=int(row["end_line"]),
                )
            )

        return results

    def clear(self):
        """Clear the database."""
        try:
            self.db.drop_table(self.table_name)
            self.table = None
        except Exception:
            pass


def parse_python_file(file_path: str) -> list[CodeChunk]:
    """
    Parse a Python file into code chunks.

    Extracts functions, classes, and module-level docstrings.
    """
    import ast

    chunks = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        lines = content.split("\n")

        # Module docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
        ):
            docstring = tree.body[0].value.value
            chunks.append(
                CodeChunk(
                    file_path=file_path,
                    content=docstring,
                    chunk_type="docstring",
                    name=Path(file_path).stem,
                    start_line=1,
                    end_line=tree.body[0].end_lineno or 1,
                )
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = node.end_lineno or start
                func_content = "\n".join(lines[start - 1 : end])

                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        content=func_content,
                        chunk_type="function",
                        name=node.name,
                        start_line=start,
                        end_line=end,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = node.end_lineno or start
                class_content = "\n".join(lines[start - 1 : end])

                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        content=class_content,
                        chunk_type="class",
                        name=node.name,
                        start_line=start,
                        end_line=end,
                    )
                )

    except Exception:
        # If parsing fails, treat whole file as one chunk
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            chunks.append(
                CodeChunk(
                    file_path=file_path,
                    content=content[:2000],  # Limit size
                    chunk_type="module",
                    name=Path(file_path).stem,
                    start_line=1,
                    end_line=content.count("\n") + 1,
                )
            )
        except Exception:
            pass

    return chunks


def index_directory(
    directory: str,
    store: LanceDBStore,
    extensions: list[str] | None = None,
) -> int:
    """
    Index all code files in a directory.

    Args:
        directory: Directory to index
        store: LanceDB store to use
        extensions: File extensions to include (default: [".py"])

    Returns:
        Number of chunks indexed
    """
    if extensions is None:
        extensions = [".py"]

    all_chunks = []

    for ext in extensions:
        for file_path in Path(directory).rglob(f"*{ext}"):
            if ".git" in str(file_path) or "__pycache__" in str(file_path):
                continue

            chunks = parse_python_file(str(file_path))
            all_chunks.extend(chunks)

    if all_chunks:
        return store.index_codebase(all_chunks)

    return 0

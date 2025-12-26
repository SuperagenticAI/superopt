#!/usr/bin/env python3
"""
LanceDB Setup Script

Sets up LanceDB for code retrieval testing with SuperOpt.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def extract_code_chunks(codebase_path: Path, chunk_size: int = 500) -> list[dict[str, Any]]:
    """
    Extract code chunks from a codebase for indexing.

    Args:
        codebase_path: Path to codebase root
        chunk_size: Target chunk size in characters

    Returns:
        List of code chunks with metadata
    """
    chunks = []

    # Supported file extensions
    code_extensions = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".rs",
        ".go",
        ".java",
        ".cpp",
        ".c",
        ".h",
    }

    for file_path in codebase_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in code_extensions:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Skip very large files
                if len(content) > 100000:
                    continue

                # Split into chunks
                lines = content.split("\n")
                current_chunk = []
                current_size = 0
                start_line = 1

                for i, line in enumerate(lines, 1):
                    current_chunk.append(line)
                    current_size += len(line)

                    if current_size >= chunk_size:
                        chunk_text = "\n".join(current_chunk)
                        chunks.append(
                            {
                                "text": chunk_text,
                                "file": str(file_path.relative_to(codebase_path)),
                                "start_line": start_line,
                                "end_line": i,
                                "language": file_path.suffix[1:],  # Remove dot
                                "metadata": {
                                    "file_path": str(file_path.relative_to(codebase_path)),
                                    "file_name": file_path.name,
                                    "line_range": f"{start_line}-{i}",
                                },
                            }
                        )
                        current_chunk = []
                        current_size = 0
                        start_line = i + 1

                # Add remaining lines as final chunk
                if current_chunk:
                    chunk_text = "\n".join(current_chunk)
                    chunks.append(
                        {
                            "text": chunk_text,
                            "file": str(file_path.relative_to(codebase_path)),
                            "start_line": start_line,
                            "end_line": len(lines),
                            "language": file_path.suffix[1:],
                            "metadata": {
                                "file_path": str(file_path.relative_to(codebase_path)),
                                "file_name": file_path.name,
                                "line_range": f"{start_line}-{len(lines)}",
                            },
                        }
                    )
            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}")
                continue

    return chunks


def generate_embeddings(
    chunks: list[dict[str, Any]], model: str = "sentence-transformers/all-MiniLM-L6-v2"
):
    """
    Generate embeddings for code chunks.

    Args:
        chunks: List of code chunks
        model: Embedding model name

    Returns:
        Chunks with embeddings added
    """
    try:
        from sentence_transformers import SentenceTransformer

        print(f"Loading embedding model: {model}")
        encoder = SentenceTransformer(model)

        texts = [chunk["text"] for chunk in chunks]
        print(f"Generating embeddings for {len(texts)} chunks...")

        embeddings = encoder.encode(texts, show_progress_bar=True)

        for chunk, embedding in zip(chunks, embeddings, strict=False):
            chunk["embedding"] = embedding.tolist()

        print(f"✓ Generated {len(embeddings)} embeddings")
        return chunks
    except ImportError:
        print(
            "Warning: sentence-transformers not installed. Install with: pip install sentence-transformers"
        )
        print("Using dummy embeddings for now...")

        # Generate dummy embeddings (for testing)
        for chunk in chunks:
            # Simple hash-based "embedding" (not real, just for structure)
            text_hash = hashlib.md5(chunk["text"].encode()).hexdigest()
            dummy_embedding = [float(int(c, 16)) / 15.0 for c in text_hash[:384]]
            chunk["embedding"] = dummy_embedding

        return chunks


def index_in_lancedb(chunks: list[dict[str, Any]], db_path: Path, table_name: str = "code_vectors"):
    """
    Index code chunks in LanceDB.

    Args:
        chunks: Code chunks with embeddings
        db_path: Path to LanceDB database
        table_name: Name of the table
    """
    try:
        import lancedb
        import pandas as pd

        print(f"Connecting to LanceDB at {db_path}")
        db = lancedb.connect(str(db_path))

        # Prepare data
        data = []
        for chunk in chunks:
            row = {
                "text": chunk["text"],
                "vector": chunk.get("embedding", []),
                "file": chunk["file"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "language": chunk["language"],
                "file_path": chunk["metadata"]["file_path"],
                "file_name": chunk["metadata"]["file_name"],
                "line_range": chunk["metadata"]["line_range"],
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Create or overwrite table
        print(f"Creating table '{table_name}' with {len(df)} chunks...")
        table = db.create_table(table_name, df, mode="overwrite")

        print(f"✓ Indexed {len(chunks)} code chunks in LanceDB")
        print(f"  Database: {db_path}")
        print(f"  Table: {table_name}")

        return table
    except ImportError:
        raise ImportError(
            "lancedb and pandas are required. Install with: pip install lancedb pandas"
        )


def main():
    parser = argparse.ArgumentParser(description="Set up LanceDB for code retrieval")
    parser.add_argument(
        "--codebase",
        type=str,
        required=True,
        help="Path to codebase to index",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./code_vectors.lancedb",
        help="Path to LanceDB database",
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default="code_vectors",
        help="Name of the table",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Target chunk size in characters",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Embedding model to use",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (use dummy embeddings)",
    )

    args = parser.parse_args()

    codebase_path = Path(args.codebase)
    if not codebase_path.exists():
        print(f"Error: Codebase path does not exist: {codebase_path}")
        return

    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Extracting code chunks from {codebase_path}...")
    chunks = extract_code_chunks(codebase_path, chunk_size=args.chunk_size)
    print(f"✓ Extracted {len(chunks)} code chunks")

    if not args.skip_embeddings:
        chunks = generate_embeddings(chunks, model=args.embedding_model)
    else:
        print("Skipping embedding generation (using dummy embeddings)")
        for chunk in chunks:
            text_hash = hashlib.md5(chunk["text"].encode()).hexdigest()
            dummy_embedding = [float(int(c, 16)) / 15.0 for c in text_hash[:384]]
            chunk["embedding"] = dummy_embedding

    # Index in LanceDB
    _table = index_in_lancedb(chunks, db_path, table_name=args.table_name)

    # Save metadata
    metadata = {
        "codebase_path": str(codebase_path),
        "num_chunks": len(chunks),
        "chunk_size": args.chunk_size,
        "embedding_model": args.embedding_model if not args.skip_embeddings else "dummy",
        "db_path": str(db_path),
        "table_name": args.table_name,
    }

    metadata_path = db_path.parent / f"{args.table_name}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n✓ Setup complete!")
    print(f"  Database: {db_path}")
    print(f"  Table: {args.table_name}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Metadata: {metadata_path}")


if __name__ == "__main__":
    main()

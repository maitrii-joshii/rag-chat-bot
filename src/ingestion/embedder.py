"""
Ingestion — Embedder (Phase 1 implementation)

Responsibilities:
  1. Load the BGE embedding model (``BAAI/bge-small-en-v1.5``) via
     ``sentence-transformers``.
  2. Generate embeddings for a list of text chunks.
  3. Upsert embeddings + metadata into the ChromaDB collection ``mf_faq_v1``.
  4. Ensure idempotency — upserting the same chunk twice does not duplicate it.

Phase 0: Stub — raises NotImplementedError.
Phase 1: Full implementation.
"""

from __future__ import annotations

from src.ingestion.loader import Document

# ── Model configuration ───────────────────────────────────────────────────────
DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME: str = "mf_faq_v1"


def embed_and_store(chunks: list[Document], vectorstore_path: str) -> int:
    """Generate embeddings and upsert chunks into ChromaDB.

    Args:
        chunks:           List of chunk Documents (from chunker.chunk).
        vectorstore_path: Filesystem path to the ChromaDB persistent store.

    Returns:
        Number of chunks upserted.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 1.
    """
    raise NotImplementedError(
        "embedder.embed_and_store is a Phase 0 stub. Full implementation in Phase 1."
    )

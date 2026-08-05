"""
Retrieval — Retriever (Phase 2 implementation)

Responsibilities:
  1. Normalise the user query (lowercase, scheme-name canonicalisation).
  2. Detect scheme name in query → apply ChromaDB metadata pre-filter.
  3. Embed query with BGE model.
  4. Search ChromaDB (cosine similarity, top-k=5, score threshold ≥ 0.65).
  5. Return a ranked list of chunks with metadata.

Phase 0: Stub — raises NotImplementedError.
Phase 2: Full implementation.
"""

from __future__ import annotations

from src.ingestion.loader import Document

# ── Retrieval configuration ───────────────────────────────────────────────────
DEFAULT_TOP_K: int = 5
DEFAULT_SCORE_THRESHOLD: float = 0.65


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    vectorstore_path: str = "./data/vectorstore",
) -> list[Document]:
    """Embed a query and retrieve the most relevant chunks from ChromaDB.

    Args:
        query:             User's natural-language question.
        top_k:             Maximum number of chunks to return.
        score_threshold:   Minimum cosine similarity to include a chunk.
        vectorstore_path:  Path to the ChromaDB persistent store.

    Returns:
        List of relevant Document chunks ordered by descending similarity score.
        Returns an empty list when no chunks meet the threshold.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 2.
    """
    raise NotImplementedError(
        "retriever.retrieve is a Phase 0 stub. Full implementation in Phase 2."
    )

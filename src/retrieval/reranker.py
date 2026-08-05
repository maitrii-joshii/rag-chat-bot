"""
Retrieval — Reranker (Phase 2 implementation — optional)

Responsibilities (optional enhancement):
  1. Accept top-k chunks from the retriever.
  2. Apply a cross-encoder model to rerank by relevance to the query.
  3. Return reranked chunks in descending order.

This module is optional for MVP — the base retriever alone is sufficient.
Phase 0: Stub — raises NotImplementedError.
Phase 2: Implement if retrieval quality requires it.
"""

from __future__ import annotations

from src.ingestion.loader import Document


def rerank(query: str, chunks: list[Document]) -> list[Document]:
    """Rerank retrieved chunks using a cross-encoder model.

    Args:
        query:  Original user query.
        chunks: Chunks returned by the retriever.

    Returns:
        Reranked list of Documents (same chunks, different order).

    Raises:
        NotImplementedError: Phase 0 stub — implement in Phase 2 if required.
    """
    raise NotImplementedError(
        "reranker.rerank is a Phase 0 stub. Implement in Phase 2 if needed."
    )

"""
Retrieval — Reranker (Phase 2 — MVP pass-through, Phase 5 enhancement)

The reranker is an optional post-retrieval step that re-orders the top-k
chunks by relevance to the query. Two modes are supported:

  Mode 1 — Pass-through (default, MVP):
    Returns chunks in the same order as the retriever. Zero extra latency.
    Sufficient when the BGE retriever already produces well-ranked results.

  Mode 2 — Cross-encoder (future enhancement):
    Uses a sentence-transformers cross-encoder to score each (query, chunk)
    pair and reorder by that score. Improves precision at the cost of latency.
    Enable by setting: RERANKER_ENABLED=true in your .env

Architecture reference: §3.5 Retriever (enhancement options)
"""

from __future__ import annotations

import logging
import os

from src.ingestion.loader import Document

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
# Set RERANKER_ENABLED=true in .env to activate cross-encoder reranking.
# Default is False (pass-through) for MVP.
_RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "false").lower() == "true"

# Cross-encoder model — only loaded when RERANKER_ENABLED=true.
# ms-marco-MiniLM-L-6-v2 is lightweight and well-suited for passage reranking.
_CROSS_ENCODER_MODEL: str = os.getenv(
    "CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Module-level model cache — loaded once on first use.
_cross_encoder_cache: dict[str, Any] = {}  # type: ignore[type-arg]

from typing import Any  # noqa: E402 — placed after the cache annotation for clarity


def rerank(query: str, chunks: list[Document]) -> list[Document]:
    """Rerank retrieved chunks by relevance to the query.

    In MVP mode (RERANKER_ENABLED=false), returns chunks unchanged.
    When RERANKER_ENABLED=true, applies a cross-encoder and reorders.

    Args:
        query:  Original (or normalised) user query.
        chunks: Documents returned by the retriever, pre-sorted by
                vector similarity score.

    Returns:
        Reranked list of Documents in descending relevance order.
        Metadata is preserved; a ``rerank_score`` key is added per chunk
        when cross-encoder mode is active.
    """
    if not chunks:
        return chunks

    if not _RERANKER_ENABLED:
        logger.debug("Reranker disabled (RERANKER_ENABLED=false) — returning chunks as-is.")
        return chunks

    return _cross_encoder_rerank(query, chunks)


def _cross_encoder_rerank(query: str, chunks: list[Document]) -> list[Document]:
    """Apply a cross-encoder to score and reorder chunks.

    Loads the cross-encoder model on first call and caches it.
    Adds a ``rerank_score`` key to each chunk's metadata.

    Args:
        query:  User query string.
        chunks: Chunks to rerank.

    Returns:
        Chunks sorted by cross-encoder score (descending).
    """
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        logger.warning(
            "sentence-transformers CrossEncoder not available — falling back to pass-through."
        )
        return chunks

    if _CROSS_ENCODER_MODEL not in _cross_encoder_cache:
        logger.info("Loading cross-encoder model: %s", _CROSS_ENCODER_MODEL)
        _cross_encoder_cache[_CROSS_ENCODER_MODEL] = CrossEncoder(_CROSS_ENCODER_MODEL)

    model = _cross_encoder_cache[_CROSS_ENCODER_MODEL]

    pairs = [(query, chunk.text) for chunk in chunks]
    scores: list[float] = model.predict(pairs).tolist()

    scored_chunks = [
        (score, chunk) for score, chunk in zip(scores, chunks)
    ]
    scored_chunks.sort(key=lambda sc: sc[0], reverse=True)

    reranked: list[Document] = []
    for score, chunk in scored_chunks:
        from copy import deepcopy
        enriched = deepcopy(chunk)
        enriched.metadata["rerank_score"] = round(float(score), 4)
        reranked.append(enriched)

    logger.info(
        "Reranked %d chunks with cross-encoder (top score: %.4f)",
        len(reranked), scored_chunks[0][0] if scored_chunks else 0.0,
    )
    return reranked

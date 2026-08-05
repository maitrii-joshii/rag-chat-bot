"""
Ingestion — Text Chunker (Phase 1 implementation)

Responsibilities:
  1. Split clean text at section boundaries (headings, double newlines).
  2. Target chunk size: ~500 tokens with ~100-token overlap.
  3. Preserve tables as single chunks (no mid-table splits).
  4. Enrich each chunk with parent document metadata:
       source_url, scheme_name, document_type, fetch_date, chunk_index.

Phase 0: Stub — raises NotImplementedError.
Phase 1: Full implementation.
"""

from __future__ import annotations

from typing import Any

from src.ingestion.loader import Document

# ── Chunk configuration ───────────────────────────────────────────────────────
CHUNK_SIZE_TOKENS: int = 500
CHUNK_OVERLAP_TOKENS: int = 100


def chunk(document: Document) -> list[Document]:
    """Split a Document into retrieval-friendly chunks.

    Args:
        document: Pre-processed Document from the loader.

    Returns:
        List of Documents — one per chunk — each inheriting parent metadata
        plus an additional ``chunk_index`` field.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 1.
    """
    raise NotImplementedError(
        "chunker.chunk is a Phase 0 stub. Full implementation in Phase 1."
    )

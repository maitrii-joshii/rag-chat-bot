"""
Ingestion — Text Pre-processor (Phase 1 implementation)

Responsibilities:
  1. Strip residual HTML tags and entities.
  2. Remove boilerplate sections (navigation, footer, legal disclaimers).
  3. Normalise whitespace (collapse multiple spaces/newlines).
  4. Return clean plain text ready for chunking.

Phase 0: Stub — raises NotImplementedError.
Phase 1: Full implementation.
"""

from __future__ import annotations


def preprocess(raw_text: str) -> str:
    """Clean and normalise raw extracted text.

    Args:
        raw_text: Text extracted by the loader (may contain HTML artefacts).

    Returns:
        Clean, normalised plain text.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 1.
    """
    raise NotImplementedError(
        "preprocessor.preprocess is a Phase 0 stub. Full implementation in Phase 1."
    )

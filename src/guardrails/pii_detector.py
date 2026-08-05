"""
Guardrails — PII Detector (Phase 3 implementation)

Regex-based detection of Personally Identifiable Information (PII) in user queries.
PII is NEVER logged or stored — the query is blocked before reaching the RAG pipeline.

Detected PII types:
  - PAN card number      : [A-Z]{5}[0-9]{4}[A-Z]
  - Aadhaar number       : 12-digit number with optional spaces
  - Indian mobile phone  : (+91 optional) [6-9]XXXXXXXXX
  - Email address        : standard RFC 5322 simplified pattern
  - Bank account number  : 9–18 digit numeric string (context-aware)

Phase 0: Pattern constants defined, detection function stubbed.
Phase 3: Full implementation with unit tests.
"""

from __future__ import annotations

import re

# ── PII Regex Patterns ────────────────────────────────────────────────────────

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "pan": re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    ),
    "aadhaar": re.compile(
        r"\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b"
    ),
    "phone": re.compile(
        r"(\+91[\s\-]?)?[6-9][0-9]{9}\b"
    ),
    "email": re.compile(
        r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
    ),
    "bank_account": re.compile(
        r"\b[0-9]{9,18}\b"
    ),
}


def detect_pii(text: str) -> dict[str, list[str]]:
    """Scan text for PII and return matches grouped by type.

    Args:
        text: User query or any free-form text to inspect.

    Returns:
        Dict mapping PII type → list of matched strings.
        Empty dict means no PII detected.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 3.

    Note:
        Bank account detection is intentionally broad (9–18 digits).
        Phase 3 will add context-aware disambiguation to reduce false positives.
    """
    raise NotImplementedError(
        "pii_detector.detect_pii is a Phase 0 stub. Full implementation in Phase 3."
    )


def contains_pii(text: str) -> bool:
    """Convenience wrapper — returns True if any PII is detected.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 3.
    """
    raise NotImplementedError(
        "pii_detector.contains_pii is a Phase 0 stub. Full implementation in Phase 3."
    )

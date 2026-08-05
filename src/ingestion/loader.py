"""
Ingestion — Document Loader (Phase 1 implementation)

Responsibilities:
  1. Fetch HTML from Groww scheme pages via HTTP GET.
  2. Enforce the domain whitelist (groww.in, hdfcfund.com, amfiindia.com, sebi.gov.in).
  3. Parse with BeautifulSoup4 — extract scheme-specific sections, discard boilerplate.
  4. Return a structured dict: {"text": str, "metadata": dict}.

Phase 0: Stub — raises NotImplementedError.
Phase 1: Full implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Document:
    """Lightweight document wrapper used throughout the RAG pipeline."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Whitelist ─────────────────────────────────────────────────────────────────
ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "groww.in",
        "hdfcfund.com",
        "amfiindia.com",
        "sebi.gov.in",
    }
)

# ── HTTP Headers ───────────────────────────────────────────────────────────────
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RAGMFBot/1.0; "
        "+https://github.com/maitrii-joshii/rag-chat-bot)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT: int = 30  # seconds


def load_url(url: str, scheme_name: str) -> Document:
    """Fetch a scheme page URL and return a Document.

    Args:
        url:         Full HTTPS URL of the scheme page (must be whitelisted).
        scheme_name: Human-readable scheme name attached to metadata.

    Returns:
        Document with extracted text and enriched metadata.

    Raises:
        ValueError: If the URL domain is not in the whitelist.
        NotImplementedError: Phase 0 stub — implemented in Phase 1.
    """
    _validate_domain(url)
    raise NotImplementedError(
        "loader.load_url is a Phase 0 stub. Full implementation in Phase 1."
    )


def _validate_domain(url: str) -> None:
    """Raise ValueError if url's domain is not in ALLOWED_DOMAINS."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    if not any(domain == allowed or domain.endswith(f".{allowed}") for allowed in ALLOWED_DOMAINS):
        raise ValueError(
            f"Domain '{domain}' is not in the allowed whitelist: {ALLOWED_DOMAINS}"
        )

"""
Generation -- Response Post-processor (Tasks 2.7 & 3.5)

Task 2.7 -- Post-processor (Phase 2):
  Validates the raw Groq LLM response against format rules, and applies
  light corrections where possible before returning. Hard failures raise
  ValueError so the generator can surface them cleanly.

Task 3.5 -- Post-Generation Validation (Phase 3):
  Scans LLM output for advisory language and PII after generation.
  Both checks are now hard failures (raise ValueError).

Checks enforced:
  1. Response is non-empty.
  2. Citation present: [Source: <url>] pattern exists.
  3. Footer present: "Last updated from sources:" line exists.
  4. Answer body does not exceed 3 sentences (soft truncation applied).
  5. No advisory language in LLM output (hard block -- Task 3.5).
  6. No PII patterns in LLM output (hard block -- Task 3.5).

Architecture reference: §7.1 Response Construction Flow, §3.7 Guardrails
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ── Regex patterns ─────────────────────────────────────────────────────────────
_CITATION_RE = re.compile(
    r"\[Source:\s*https?://[^\]]+\]",
    re.IGNORECASE,
)
_FOOTER_RE = re.compile(
    r"Last\s+updated\s+from\s+sources\s*:\s*.+",
    re.IGNORECASE,
)
# Sentence boundary splitter (used in _split_sentences below)
# Splits on punctuation followed by whitespace -- abbrev/decimal handling done in the splitter.
# Advisory language patterns (Phase 3 extension point -- pre-compiled here)
_ADVISORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(you should|i recommend|i suggest|my advice|invest in)\b", re.I),
    re.compile(r"\b(better than|outperform|superior to|best fund|top fund)\b", re.I),
    re.compile(r"\b(will give|will return|expected to|projected to)\b", re.I),
]

# No-information response prefix (exempt from citation check)
_NO_INFO_PREFIX = "I don't have that information"


def validate_response(response: str) -> str:
    """Validate and lightly correct the raw LLM response.

    Corrections applied automatically:
      - Truncates the answer body to 3 sentences if exceeded (preserves citation + footer).
      - Strips leading/trailing whitespace.

    Hard failures (raise ValueError -- generator returns NO_INFORMATION_RESPONSE):
      - Empty or whitespace-only response.
      - No citation URL ([Source: ...]) found.
      - No "Last updated from sources:" footer found.
      - Advisory language detected in response body.

    Args:
        response: Raw string returned by the Groq LLM.

    Returns:
        Validated (and lightly corrected) response string.

    Raises:
        ValueError: If the response fails a hard validation check.
    """
    if not response or not response.strip():
        raise ValueError("LLM returned an empty response.")

    response = response.strip()

    # Exempt the no-information fallback from citation/footer checks --
    # it is generated locally, not by the LLM.
    if response.startswith(_NO_INFO_PREFIX):
        logger.debug("No-information response detected -- skipping citation/footer checks.")
        return response

    # ── Check 1: Citation present ─────────────────────────────────────────────
    citation_match = _CITATION_RE.search(response)
    if not citation_match:
        logger.warning("LLM response missing [Source: <url>] citation: %r", response[:120])
        raise ValueError(
            "LLM response is missing a required [Source: <url>] citation. "
            "Response will not be served."
        )

    # ── Check 2: Footer present ───────────────────────────────────────────────
    footer_match = _FOOTER_RE.search(response)
    if not footer_match:
        logger.warning("LLM response missing 'Last updated from sources:' footer.")
        raise ValueError(
            "LLM response is missing the required 'Last updated from sources:' footer."
        )

    # ── Check 3: Advisory language (Task 3.5 -- hard block) ────────────────────
    for pattern in _ADVISORY_PATTERNS:
        match = pattern.search(response)
        if match:
            logger.error(
                "Advisory language detected in LLM output (blocked): %r",
                match.group(0),
            )
            raise ValueError(
                f"LLM response contains advisory language ({match.group(0)!r}) "
                "and cannot be served. This is a post-generation safety violation."
            )

    # ── Check 4: PII in LLM output (Task 3.5 -- hard block) ──────────────────
    from src.guardrails.pii_detector import detect_pii
    pii_found = detect_pii(response)
    if pii_found:
        pii_types = list(pii_found.keys())
        logger.error("PII detected in LLM output (blocked): types=%s", pii_types)
        raise ValueError(
            f"LLM response contains PII ({pii_types}) and cannot be served. "
            "This is a post-generation safety violation."
        )

    # ── Check 4: Sentence count (soft truncation) ─────────────────────────────
    response = _enforce_sentence_limit(response, max_sentences=3)

    logger.debug("Response validated successfully (%d chars).", len(response))
    return response


def _enforce_sentence_limit(response: str, max_sentences: int = 3) -> str:
    """Truncate the answer body to max_sentences, preserving citation + footer.

    Strategy:
      1. Split the response into: answer body | citation | footer.
      2. Count sentences in the answer body only.
      3. If > max_sentences, truncate at the nth sentence boundary.
      4. Reassemble with the original citation and footer.

    Args:
        response:      Validated LLM response string.
        max_sentences: Maximum sentences allowed in the answer body.

    Returns:
        Potentially truncated response string.
    """
    # Separate citation and footer from the answer body
    citation_match = _CITATION_RE.search(response)
    footer_match = _FOOTER_RE.search(response)

    # Use positions to carve out the body
    body_end = len(response)
    if citation_match:
        body_end = min(body_end, citation_match.start())
    if footer_match:
        body_end = min(body_end, footer_match.start())

    body = response[:body_end].strip()
    tail = response[body_end:].strip()

    # Split body into sentences
    sentences: list[str] = _split_sentences(body)

    if len(sentences) <= max_sentences:
        return response  # No truncation needed

    logger.info(
        "Truncating LLM response from %d sentences to %d.",
        len(sentences), max_sentences,
    )
    truncated_body = " ".join(s.strip() for s in sentences[:max_sentences])
    if not truncated_body.endswith((".", "!", "?")):
        truncated_body += "."

    return f"{truncated_body}\n\n{tail}" if tail else truncated_body


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using a simple but robust regex splitter.

    Handles common abbreviations (Rs., Mr., e.g.) and decimal numbers
    (0.68%, Rs. 500) to avoid false splits.

    Args:
        text: Plain-text string to split.

    Returns:
        List of sentence strings (non-empty, stripped).
    """
    # Split on sentence-ending punctuation followed by whitespace
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_citation_url(response: str) -> str | None:
    """Extract the citation URL from a validated response.

    Used by the API to return structured citation data.

    Args:
        response: Validated LLM response string.

    Returns:
        The URL string inside [Source: <url>], or None if not found.
    """
    match = _CITATION_RE.search(response)
    if not match:
        return None
    # Strip the [Source: ...] wrapper to get just the URL
    raw = match.group(0)                          # e.g. "[Source: https://groww.in/...]"
    url = re.sub(r"^\[Source:\s*|\]$", "", raw, flags=re.IGNORECASE).strip()
    return url


def extract_last_updated(response: str) -> str | None:
    """Extract the 'Last updated from sources: <date>' value from a response.

    Args:
        response: Validated LLM response string.

    Returns:
        The date string after the footer label, or None if not found.
    """
    match = _FOOTER_RE.search(response)
    if not match:
        return None
    footer_line = match.group(0)
    parts = footer_line.split(":", 1)
    return parts[1].strip() if len(parts) > 1 else None

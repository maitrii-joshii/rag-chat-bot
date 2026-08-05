"""
Ingestion — Text Pre-processor (Task 1.3)

Responsibilities:
  1. Strip residual HTML tags and decode HTML entities.
  2. Remove boilerplate patterns (page numbers, legal footers, repeated disclaimers).
  3. Normalise whitespace: collapse multiple spaces/newlines to single separators.
  4. Return clean plain text ready for the chunker.
"""

from __future__ import annotations

import html
import logging
import re

logger = logging.getLogger(__name__)

# ── Boilerplate Patterns to Strip ─────────────────────────────────────────────
# These are common Groww / financial page artefacts that add noise without value.
_BOILERPLATE_PATTERNS: list[re.Pattern[str]] = [
    # Page numbers: "Page 1 of 5", "1 / 5"
    re.compile(r"\bPage\s+\d+\s+of\s+\d+\b", re.I),
    re.compile(r"\b\d+\s*/\s*\d+\b"),

    # "Read more", "Show more", "See all" UI fragments
    re.compile(r"\b(Read|Show|See|View)\s+(more|all|less|details?)\b", re.I),

    # "Last updated: ..." lines (we attach our own fetch_date)
    re.compile(r"Last\s+updated[:\s]+[\w\s,/-]+", re.I),

    # "Disclaimer: ..." paragraphs (long)
    re.compile(r"Disclaimer[:\s].{20,}", re.I),

    # "Mutual fund investments are subject to market risks..." standard disclaimer
    re.compile(
        r"Mutual\s+fund\s+investments?\s+are\s+subject\s+to\s+market\s+risk.*?before\s+investing\.?",
        re.I | re.DOTALL,
    ),

    # AMFI / SEBI boilerplate registration numbers
    re.compile(r"(AMFI|SEBI)\s+Reg(istration)?\s*(No\.?|Number)?\s*:?\s*[\w/\-]+", re.I),

    # CIN / GSTIN lines
    re.compile(r"\b(CIN|GSTIN|PAN)\s*[:\-]?\s*[A-Z0-9]+\b"),

    # Repeated "|" separators (nav bars that got through)
    re.compile(r"(\s*\|\s*){3,}"),

    # "Cookie", "Privacy Policy", "Terms & Conditions" fragments
    re.compile(r"\b(Cookie|Privacy\s+Policy|Terms\s+(and|&)\s+Conditions|Copyright)\b.*", re.I),

    # Excessive dashes / underscores used as visual dividers
    re.compile(r"[-_]{4,}"),

    # "Click here", "Learn more", "Apply now" CTA fragments
    re.compile(r"\b(Click|Tap)\s+here\b.*", re.I),
    re.compile(r"\bApply\s+now\b.*", re.I),

    # Download app prompts
    re.compile(r"\b(Download|Get)\s+(the\s+)?(Groww\s+)?(app|application)\b.*", re.I),
]

# ── Residual HTML Tag Pattern ─────────────────────────────────────────────────
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# ── Whitespace Normalization ──────────────────────────────────────────────────
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def preprocess(raw_text: str) -> str:
    """Clean and normalise raw extracted text for chunking.

    Pipeline:
      1. Decode HTML entities (e.g. &amp; → &, &nbsp; → space).
      2. Strip any residual HTML tags (the loader may leave some).
      3. Apply boilerplate removal patterns.
      4. Normalise whitespace (collapse spaces and excess newlines).
      5. Strip leading/trailing whitespace.

    Args:
        raw_text: Text extracted by the loader. May contain HTML artefacts,
                  boilerplate, and inconsistent whitespace.

    Returns:
        Clean, normalised plain text ready for ``chunker.chunk()``.
        Returns an empty string if the input is empty or all boilerplate.
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text

    # Step 1 — Decode HTML entities
    text = html.unescape(text)

    # Step 2 — Strip residual HTML tags
    text = _HTML_TAG_RE.sub(" ", text)

    # Step 3 — Remove boilerplate patterns
    for pattern in _BOILERPLATE_PATTERNS:
        text = pattern.sub(" ", text)

    # Step 4 — Normalise whitespace
    text = _MULTI_SPACE_RE.sub(" ", text)    # collapse inline spaces/tabs
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)  # max 2 consecutive newlines

    # Step 5 — Strip edges
    text = text.strip()

    char_count = len(text)
    logger.debug("Preprocessed text: %d chars", char_count)

    if char_count < 50:
        logger.warning(
            "Preprocessed text is very short (%d chars) — may indicate loader issues",
            char_count,
        )

    return text

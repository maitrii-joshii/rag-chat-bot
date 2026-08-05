"""
Guardrails — Intent Classifier (Phase 3 implementation)

Keyword-based classification of user queries into:
  - FACTUAL       : Proceed to RAG pipeline.
  - ADVISORY      : Politely refused (should I invest, recommend, is it good...).
  - COMPARISON    : Politely refused (which is better, compare X and Y...).
  - PREDICTION    : Politely refused (will it give returns, future performance...).
  - BUY_SELL      : Politely refused (should I buy, time to sell...).
  - OUT_OF_SCOPE  : Politely refused (non-mutual-fund queries).

Phase 0: Pattern constants defined, classification functions stubbed.
Phase 3: Full implementation with unit tests.
"""

from __future__ import annotations

import re
from enum import Enum


class QueryIntent(str, Enum):
    """Enumeration of recognised query intent categories."""

    FACTUAL = "factual"
    ADVISORY = "advisory"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    BUY_SELL = "buy_sell"
    OUT_OF_SCOPE = "out_of_scope"


# ── Advisory Patterns ─────────────────────────────────────────────────────────

_ADVISORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshould\s+i\s+invest\b", re.I),
    re.compile(r"\brecommend\s+a?\s*fund\b", re.I),
    re.compile(r"\bis\s+it\s+a\s+good\b", re.I),
    re.compile(r"\badvise\b", re.I),
    re.compile(r"\bworth\s+investing\b", re.I),
]

_COMPARISON_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bwhich\s+is\s+better\b", re.I),
    re.compile(r"\bcompare\b", re.I),
    re.compile(r"\bbest\s+fund\s+for\b", re.I),
    re.compile(r"\bvs\.?\b", re.I),
    re.compile(r"\bversus\b", re.I),
]

_PREDICTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bwill\s+it\s+give\b", re.I),
    re.compile(r"\bfuture\s+performance\b", re.I),
    re.compile(r"\bexpected\s+nav\b", re.I),
    re.compile(r"\bwill\s+(the\s+)?fund\b", re.I),
    re.compile(r"\bforecast\b", re.I),
    re.compile(r"\bpredict\b", re.I),
]

_BUY_SELL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshould\s+i\s+buy\b", re.I),
    re.compile(r"\btime\s+to\s+sell\b", re.I),
    re.compile(r"\bentry\s+point\b", re.I),
    re.compile(r"\bwhen\s+to\s+(buy|sell|exit|redeem)\b", re.I),
    re.compile(r"\bshould\s+i\s+(sell|redeem|exit)\b", re.I),
]

# ── Mutual-fund topic keywords (out-of-scope detection) ───────────────────────
_MF_TOPIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(mutual\s+fund|nav|expense\s+ratio|exit\s+load|sip|lump\s+?sum)\b", re.I),
    re.compile(r"\b(hdfc|scheme|amc|fund\s+house|folio|redemption|units)\b", re.I),
    re.compile(r"\b(small\s+cap|large\s+cap|mid\s+cap|debt|index\s+fund|etf)\b", re.I),
]


def classify(query: str) -> QueryIntent:
    """Classify the user query into an intent category.

    Args:
        query: Raw user query string.

    Returns:
        A QueryIntent enum value.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 3.
    """
    raise NotImplementedError(
        "intent_classifier.classify is a Phase 0 stub. Full implementation in Phase 3."
    )


def is_factual(query: str) -> bool:
    """Return True if the query is classified as FACTUAL.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 3.
    """
    raise NotImplementedError(
        "intent_classifier.is_factual is a Phase 0 stub. Full implementation in Phase 3."
    )

"""
Guardrails -- Intent Classifier (Tasks 3.2 & 3.3)

Task 3.2 -- Advisory Intent Classifier:
  Keyword-based classification of advisory, comparison, prediction, and
  buy/sell queries.

Task 3.3 -- Out-of-Scope Detector:
  Detects queries that are unrelated to mutual funds / HDFC schemes.
  Strategy: if none of the MF topic keywords are present AND the query
  doesn't look like a factual fund question, classify as OUT_OF_SCOPE.

Classification priority (highest to lowest):
  1. ADVISORY      -- "should I invest", "recommend", "is it a good fund"
  2. COMPARISON    -- "which is better", "compare", "vs", "versus"
  3. PREDICTION    -- "will it give returns", "future performance"
  4. BUY_SELL      -- "should I buy", "time to sell", "when to exit"
  5. OUT_OF_SCOPE  -- non-mutual-fund topic
  6. FACTUAL       -- everything else (proceed to RAG pipeline)

Architecture reference: §8.1 Classification Taxonomy, §8.2 Advisory Detection
"""

from __future__ import annotations

import re
from enum import Enum


class QueryIntent(str, Enum):
    """Enumeration of recognised query intent categories."""

    FACTUAL     = "factual"
    ADVISORY    = "advisory"
    COMPARISON  = "comparison"
    PREDICTION  = "prediction"
    BUY_SELL    = "buy_sell"
    GREETING    = "greeting"
    OUT_OF_SCOPE = "out_of_scope"


# ── Task 3.2: Advisory Patterns ───────────────────────────────────────────────
_ADVISORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshould\s+i\s+invest\b", re.I),
    re.compile(r"\brecommend\s+(?:a\s+)?fund\b", re.I),
    re.compile(r"\brecommend(?:ation)?\b", re.I),
    re.compile(r"\bshould\s+i\s+(?:go\s+for|choose|pick|select)\b", re.I),
    re.compile(r"\bis\s+it\s+(?:a\s+)?good\s+(?:fund|investment|option|bet)\b", re.I),
    re.compile(r"\ba\s+good\s+(?:investment|fund|option|bet)\b", re.I),
    re.compile(r"\bworth\s+investing\b", re.I),
    re.compile(r"\badvise?\b", re.I),
    re.compile(r"\bsuggestion\b", re.I),
    re.compile(r"\bwhere\s+(?:should|to)\s+invest\b", re.I),
    re.compile(r"\bwhich\s+fund\s+(?:should|is\s+good|to\s+buy|to\s+invest)\b", re.I),
    re.compile(r"\bgood\s+(?:fund|investment)\s+(?:for|to)\b", re.I),
    re.compile(r"\bbest\s+(?:fund|option|choice)\s+for\s+me\b", re.I),
    re.compile(r"\bshould\s+i\b(?!.*\b(?:buy|sell|exit|redeem|switch)\b).*\bfund\b", re.I),
]

# ── Comparison Patterns ────────────────────────────────────────────────────────
_COMPARISON_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bwhich\s+is\s+better\b", re.I),
    re.compile(r"\bcompare\b", re.I),
    re.compile(r"\bbetter\s+than\b", re.I),
    re.compile(r"\bbest\s+fund\s+(?:for|in|among)\b", re.I),
    re.compile(r"\b(?:vs|versus)\b", re.I),
    re.compile(r"\bor\s+(?:hdfc|the)\b.*\bfund\b", re.I),
    re.compile(r"\bdifference\s+between\b", re.I),
    re.compile(r"\bsuperior\b", re.I),
]

# ── Prediction Patterns ────────────────────────────────────────────────────────
_PREDICTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bwill\s+(?:it|this|the\s+fund)\s+give\b", re.I),
    re.compile(r"\bwill\s+(?:hdfc|the\s+fund|this\s+fund)\b", re.I),
    re.compile(r"\bfuture\s+(?:performance|returns?|nav)\b", re.I),
    re.compile(r"\bexpected\s+(?:returns?|nav|performance)\b", re.I),
    re.compile(r"\bforecast\b", re.I),
    re.compile(r"\bpredict\b", re.I),
    re.compile(r"\bprojected\b", re.I),
    re.compile(r"\btarget\s+(?:nav|price|return)\b", re.I),
    re.compile(r"\bcan\s+i\s+(?:expect|get)\b.*%", re.I),
    re.compile(r"\bhow\s+much\s+(?:will|can)\b.*(?:return|give|grow)\b", re.I),
]

# ── Buy / Sell Patterns ────────────────────────────────────────────────────────
_BUY_SELL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bshould\s+i\s+(?:buy|sell|redeem|exit|switch)\b", re.I),
    re.compile(r"\btime\s+to\s+(?:buy|sell|exit|redeem)\b", re.I),
    re.compile(r"\bentry\s+(?:point|level)\b", re.I),
    re.compile(r"\bexit\s+(?:point|level|now)\b", re.I),
    re.compile(r"\bwhen\s+(?:to|should\s+i)\s+(?:buy|sell|exit|redeem|switch)\b", re.I),
    re.compile(r"\bbook\s+(?:profits?|gains?|losses?)\b", re.I),
    re.compile(r"\bswitch\s+(?:out|from)\b", re.I),
    re.compile(r"\bpartial\s+(?:redemption|withdrawal|exit)\b", re.I),
]

# ── Greeting Patterns ──────────────────────────────────────────────────────────
_GREETING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(?:hello|hi|hey|good\s+(?:morning|afternoon|evening|day)|greetings|namaste)[!\.\,\s]*$", re.I),
]

# ── Task 3.3: Mutual-Fund Topic Keywords (Out-of-Scope Detection) ─────────────
# A query is in-scope if it contains at least one of these keyword patterns.
_MF_TOPIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(mutual\s+fund|nav|net\s+asset\s+value)\b", re.I),
    re.compile(r"\b(expense\s+ratio|exit\s+load|entry\s+load)\b", re.I),
    re.compile(r"\b(sip|lump\s*sum|systematic\s+investment)\b", re.I),
    re.compile(r"\b(hdfc|hdfcfund|amc|fund\s+house)\b", re.I),
    re.compile(r"\b(scheme|folio|redemption|units?|corpus)\b", re.I),
    re.compile(r"\b(small\s+cap|large\s+cap|mid\s+cap|flexi\s+cap|multi\s+cap)\b", re.I),
    re.compile(r"\b(index\s+fund|etf|debt\s+fund|hybrid\s+fund)\b", re.I),
    re.compile(r"\b(sensex|nifty|bse|nse)\b", re.I),
    re.compile(r"\b(fund\s+manager|portfolio|holding|sectoral)\b", re.I),
    re.compile(r"\b(cagr|returns?|annuali[sz]ed|benchmark)\b", re.I),
    re.compile(r"\b(sebi|amfi|rta|cams|kfintech)\b", re.I),
    re.compile(r"\b(stamp\s+duty|tax|elss|lock.?in|demat)\b", re.I),
    re.compile(r"\b(gold|pharma|defence|balanced\s+advantage|short\s+term)\b", re.I),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def classify(query: str) -> QueryIntent:
    """Classify the user query into an intent category.

    Priority order (first match wins):
      ADVISORY > COMPARISON > PREDICTION > BUY_SELL > OUT_OF_SCOPE > FACTUAL

    Args:
        query: Raw user query string.

    Returns:
        A QueryIntent enum value.
    """
    # Priority 1: Buy / Sell (checked first to avoid being swallowed by broad advisory)
    for pattern in _BUY_SELL_PATTERNS:
        if pattern.search(query):
            return QueryIntent.BUY_SELL

    # Priority 2: Advisory
    for pattern in _ADVISORY_PATTERNS:
        if pattern.search(query):
            return QueryIntent.ADVISORY

    # Priority 3: Comparison
    for pattern in _COMPARISON_PATTERNS:
        if pattern.search(query):
            return QueryIntent.COMPARISON

    # Priority 4: Prediction
    for pattern in _PREDICTION_PATTERNS:
        if pattern.search(query):
            return QueryIntent.PREDICTION

    # Priority 5: Greeting
    for pattern in _GREETING_PATTERNS:
        if pattern.search(query):
            return QueryIntent.GREETING

    # Priority 6: Out-of-Scope (Task 3.3)
    if not _is_mf_related(query):
        return QueryIntent.OUT_OF_SCOPE

    # Priority 6: Default -- factual fund question
    return QueryIntent.FACTUAL


def is_factual(query: str) -> bool:
    """Return True if the query is classified as FACTUAL.

    Args:
        query: Raw user query string.

    Returns:
        True only for FACTUAL queries; False for all refused intents.
    """
    return classify(query) == QueryIntent.FACTUAL


def is_blocked(query: str) -> bool:
    """Return True if the query should be refused (not FACTUAL).

    Args:
        query: Raw user query string.

    Returns:
        True if the query should be refused; False if it may proceed to RAG.
    """
    return classify(query) != QueryIntent.FACTUAL


# ── Task 3.3: Out-of-Scope Helper ─────────────────────────────────────────────

def _is_mf_related(query: str) -> bool:
    """Return True if the query contains mutual-fund topic keywords.

    A query is considered in-scope if it matches at least one MF topic pattern.
    This guards against completely off-topic queries (weather, sports, etc.)
    while being permissive about phrasings of genuine fund questions.

    Args:
        query: Normalised or raw user query string.

    Returns:
        True if the query is about mutual funds / fund schemes.
    """
    for pattern in _MF_TOPIC_PATTERNS:
        if pattern.search(query):
            return True
    return False

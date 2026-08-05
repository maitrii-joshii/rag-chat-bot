"""
Guardrails — Refusal Handler (Phase 3 implementation)

Generates polite, context-appropriate refusal responses for:
  - Advisory queries    ("Should I invest in...?")
  - Comparison queries  ("Which is better — X or Y?")
  - Prediction queries  ("Will HDFC Defence Fund give 20% returns?")
  - Buy/Sell queries    ("Should I sell now?")
  - Out-of-scope queries("What is the weather today?")
  - PII-detected queries("My PAN is ABCDE1234F")

All refusals include the AMFI fallback link and a "Last updated" footer.

Phase 0: Response templates defined, handler function stubbed.
Phase 3: Full implementation with unit tests.
"""

from __future__ import annotations

from src.guardrails.intent_classifier import QueryIntent

# ── AMFI Fallback Link ────────────────────────────────────────────────────────
AMFI_URL: str = "https://www.amfiindia.com"

# ── Refusal Templates ─────────────────────────────────────────────────────────
_REFUSAL_TEMPLATES: dict[QueryIntent | str, str] = {
    QueryIntent.ADVISORY: (
        "I'm a facts-only assistant and cannot provide investment advice. "
        f"For personalised guidance, please consult a SEBI-registered financial adviser "
        f"or visit {AMFI_URL} for educational resources. "
        f"Last updated from sources: N/A"
    ),
    QueryIntent.COMPARISON: (
        "I'm unable to compare funds or make recommendations. "
        f"I can share factual details (NAV, expense ratio, exit load) about individual HDFC schemes. "
        f"Visit {AMFI_URL} for comparison tools. "
        f"Last updated from sources: N/A"
    ),
    QueryIntent.PREDICTION: (
        "Predicting future fund performance is outside my scope. "
        f"I answer only factual questions about current HDFC scheme details. "
        f"For historical data, visit {AMFI_URL}. "
        f"Last updated from sources: N/A"
    ),
    QueryIntent.BUY_SELL: (
        "I cannot advise on when to buy, sell, or redeem investments. "
        f"Please consult a SEBI-registered financial adviser. "
        f"For fund details, visit {AMFI_URL}. "
        f"Last updated from sources: N/A"
    ),
    QueryIntent.OUT_OF_SCOPE: (
        "I can only answer factual questions about HDFC Mutual Fund schemes. "
        f"Your question appears to be outside that scope. "
        f"Visit {AMFI_URL} for mutual fund information. "
        f"Last updated from sources: N/A"
    ),
    "pii": (
        "Your message appears to contain personal information (PAN, Aadhaar, phone, etc.). "
        "For your security, please do not share personal details in this chat. "
        f"Last updated from sources: N/A"
    ),
}


def build_refusal(intent: QueryIntent | str) -> str:
    """Return the appropriate refusal response for a given intent.

    Args:
        intent: A QueryIntent value or the string ``"pii"`` for PII-blocked queries.

    Returns:
        Polite refusal string including the AMFI link and "Last updated" footer.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 3.
    """
    raise NotImplementedError(
        "refusal_handler.build_refusal is a Phase 0 stub. Full implementation in Phase 3."
    )

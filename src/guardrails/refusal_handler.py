"""
Guardrails -- Refusal Handler (Task 3.4)

Generates polite, context-appropriate refusal responses for all non-FACTUAL
query intents. Every refusal:
  - Is tailored to the specific intent type (advisory / comparison / etc.)
  - Includes the mandatory AMFI fallback URL: https://www.amfiindia.com

Architecture reference: §7.3 Refusal Response Schema
"""

from __future__ import annotations

from src.guardrails.intent_classifier import QueryIntent

# ── AMFI Fallback URL (mandatory in all refusals per architecture §7.3) ───────
AMFI_URL: str = "https://www.amfiindia.com"

# ── Refusal Templates (Task 3.4) ──────────────────────────────────────────────
# Each template is a single-string refusal response. All include AMFI_URL.
_REFUSAL_TEMPLATES: dict[str | QueryIntent, str] = {
    QueryIntent.ADVISORY: (
        "I'm a facts-only assistant and cannot provide investment advice or recommendations. "
        f"For personalised guidance, please consult a SEBI-registered financial adviser "
        f"or visit {AMFI_URL} for educational resources on mutual funds."
    ),
    QueryIntent.COMPARISON: (
        "I'm unable to compare funds or make fund recommendations. "
        "I can share individual factual details — such as NAV, expense ratio, "
        "exit load, or minimum SIP — for any HDFC scheme you ask about. "
        f"For fund comparison tools, visit {AMFI_URL}."
    ),
    QueryIntent.PREDICTION: (
        "Predicting future fund performance or returns is outside my scope. "
        "I can only answer factual questions about current HDFC scheme details "
        "(expense ratio, exit load, NAV, minimum SIP, etc.). "
        f"For historical NAV data, visit {AMFI_URL}."
    ),
    QueryIntent.BUY_SELL: (
        "I cannot advise on when to buy, sell, redeem, or switch investments. "
        "Please consult a SEBI-registered financial adviser for timing decisions. "
        f"For fund details, visit {AMFI_URL}."
    ),
    QueryIntent.OUT_OF_SCOPE: (
        "I can only answer factual questions about HDFC Mutual Fund schemes "
        "(expense ratio, exit load, NAV, minimum SIP, fund manager, etc.). "
        "Your question appears to be outside that scope. "
        f"For mutual fund information, visit {AMFI_URL}."
    ),
    # PII-blocked: deliberately does NOT echo back PII values
    "pii": (
        "Your message appears to contain personal information "
        "(such as a PAN, Aadhaar, phone number, or email address). "
        "For your security, please do not share personal details in this chat. "
        "I can answer factual questions about HDFC Mutual Fund schemes."
    ),
}


def build_refusal(intent: QueryIntent | str) -> str:
    """Return the appropriate refusal response for a given intent.

    Args:
        intent: A QueryIntent enum value, or the string ``"pii"`` for
                queries blocked due to detected PII.

    Returns:
        Polite refusal string. Always includes the AMFI URL.

    Raises:
        ValueError: If ``intent`` is not a recognised QueryIntent value
                    or the string ``"pii"``.
    """
    # Normalise string inputs to QueryIntent where possible
    if isinstance(intent, str) and intent != "pii":
        try:
            intent = QueryIntent(intent)
        except ValueError:
            raise ValueError(
                f"Unknown intent: {intent!r}. "
                f"Must be a QueryIntent value or 'pii'. "
                f"Got: {list(QueryIntent) + ['pii']}"
            )

    template = _REFUSAL_TEMPLATES.get(intent)
    if template is None:
        raise ValueError(
            f"No refusal template defined for intent: {intent!r}. "
            f"Supported: {list(_REFUSAL_TEMPLATES.keys())}"
        )

    return template

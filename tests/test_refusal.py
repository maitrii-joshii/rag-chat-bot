"""
tests/test_refusal.py -- Unit Tests for Refusal Handler (Task 3.6)

Covers:
  - build_refusal() returns non-empty string for every QueryIntent
  - All refusals contain the mandatory AMFI URL
  - All refusals contain the "Last updated from sources:" footer
  - PII refusal does not echo back PII values
  - No refusal contains investment advice language
  - Invalid intent raises ValueError
"""

from __future__ import annotations

import pytest

from src.guardrails.intent_classifier import QueryIntent
from src.guardrails.refusal_handler import build_refusal, AMFI_URL

FOOTER_MARKER = "Last updated from sources:"
ADVICE_PHRASES = [
    "you should invest",
    "i recommend",
    "buy this fund",
    "guaranteed returns",
]

ALL_INTENTS = [
    QueryIntent.ADVISORY,
    QueryIntent.COMPARISON,
    QueryIntent.PREDICTION,
    QueryIntent.BUY_SELL,
    QueryIntent.OUT_OF_SCOPE,
]


# ─────────────────────────────────────────────────────────────────────────────
# Refusal Handler Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRefusalHandler:
    """Tests for src.guardrails.refusal_handler"""

    # ── Non-empty checks ──────────────────────────────────────────────────────
    def test_advisory_refusal_is_non_empty(self):
        assert len(build_refusal(QueryIntent.ADVISORY)) > 0

    def test_comparison_refusal_is_non_empty(self):
        assert len(build_refusal(QueryIntent.COMPARISON)) > 0

    def test_prediction_refusal_is_non_empty(self):
        assert len(build_refusal(QueryIntent.PREDICTION)) > 0

    def test_buy_sell_refusal_is_non_empty(self):
        assert len(build_refusal(QueryIntent.BUY_SELL)) > 0

    def test_out_of_scope_refusal_is_non_empty(self):
        assert len(build_refusal(QueryIntent.OUT_OF_SCOPE)) > 0

    def test_pii_refusal_is_non_empty(self):
        assert len(build_refusal("pii")) > 0

    # ── AMFI URL in all refusals ──────────────────────────────────────────────
    def test_advisory_refusal_contains_amfi_link(self):
        assert AMFI_URL in build_refusal(QueryIntent.ADVISORY)

    def test_comparison_refusal_contains_amfi_link(self):
        assert AMFI_URL in build_refusal(QueryIntent.COMPARISON)

    def test_prediction_refusal_contains_amfi_link(self):
        assert AMFI_URL in build_refusal(QueryIntent.PREDICTION)

    def test_buy_sell_refusal_contains_amfi_link(self):
        assert AMFI_URL in build_refusal(QueryIntent.BUY_SELL)

    def test_out_of_scope_refusal_contains_amfi_link(self):
        assert AMFI_URL in build_refusal(QueryIntent.OUT_OF_SCOPE)

    # ── Footer present in all refusals ────────────────────────────────────────
    def test_advisory_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal(QueryIntent.ADVISORY)

    def test_comparison_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal(QueryIntent.COMPARISON)

    def test_prediction_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal(QueryIntent.PREDICTION)

    def test_buy_sell_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal(QueryIntent.BUY_SELL)

    def test_out_of_scope_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal(QueryIntent.OUT_OF_SCOPE)

    def test_pii_refusal_has_footer(self):
        assert FOOTER_MARKER in build_refusal("pii")

    # ── PII refusal safety ────────────────────────────────────────────────────
    def test_pii_refusal_does_not_repeat_pii(self):
        """PII refusal must NOT echo back actual PII values."""
        response = build_refusal("pii")
        # The response should not contain example PAN, phone, or Aadhaar values
        assert "ABCDE1234F" not in response
        assert "9876543210" not in response
        assert "1234 5678 9012" not in response

    def test_pii_refusal_mentions_personal_information(self):
        """PII refusal should reference 'personal information'."""
        assert "personal" in build_refusal("pii").lower()

    # ── No investment advice in any refusal ───────────────────────────────────
    def test_no_refusal_gives_investment_advice(self):
        """No refusal response should contain investment advice phrases."""
        for intent in ALL_INTENTS:
            response = build_refusal(intent).lower()
            for phrase in ADVICE_PHRASES:
                assert phrase not in response, (
                    f"Refusal for {intent} contains advice phrase: {phrase!r}"
                )

    def test_pii_refusal_gives_no_investment_advice(self):
        response = build_refusal("pii").lower()
        for phrase in ADVICE_PHRASES:
            assert phrase not in response

    # ── Error handling ────────────────────────────────────────────────────────
    def test_invalid_intent_raises_value_error(self):
        with pytest.raises(ValueError):
            build_refusal("unknown_intent")

    def test_factual_intent_raises_value_error(self):
        """FACTUAL queries should not receive refusals -- raises ValueError."""
        with pytest.raises(ValueError):
            build_refusal(QueryIntent.FACTUAL)

    # ── String input normalisation ────────────────────────────────────────────
    def test_string_advisory_works(self):
        """build_refusal('advisory') should normalise to QueryIntent.ADVISORY."""
        assert build_refusal("advisory") == build_refusal(QueryIntent.ADVISORY)

    def test_string_comparison_works(self):
        assert build_refusal("comparison") == build_refusal(QueryIntent.COMPARISON)

    def test_string_out_of_scope_works(self):
        assert build_refusal("out_of_scope") == build_refusal(QueryIntent.OUT_OF_SCOPE)

"""
tests/test_refusal.py — Unit Tests for Refusal Handler (Phase 3)

Tests:
  - build_refusal() returns a non-empty string for every QueryIntent
  - All refusal responses include the AMFI fallback URL
  - All refusal responses include the "Last updated from sources:" footer
  - PII-blocked refusal is distinct and appropriate
  - No refusal response contains investment advice language

Phase 0: Test skeleton with placeholder assertions.
Phase 3: Full test implementation after refusal_handler is built.
"""

from __future__ import annotations

import pytest


AMFI_URL = "https://www.amfiindia.com"
FOOTER_MARKER = "Last updated from sources:"


# ─────────────────────────────────────────────────────────────────────────────
# Refusal Handler Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRefusalHandler:
    """Tests for src.guardrails.refusal_handler"""

    def test_advisory_refusal_is_non_empty(self):
        """build_refusal(ADVISORY) should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_advisory_refusal_contains_amfi_link(self):
        """Advisory refusal must include the AMFI URL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_advisory_refusal_has_footer(self):
        """Advisory refusal must end with 'Last updated from sources:'."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_comparison_refusal_is_non_empty(self):
        """build_refusal(COMPARISON) should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_comparison_refusal_contains_amfi_link(self):
        """Comparison refusal must include the AMFI URL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_prediction_refusal_is_non_empty(self):
        """build_refusal(PREDICTION) should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_prediction_refusal_has_footer(self):
        """Prediction refusal must end with 'Last updated from sources:'."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_buy_sell_refusal_is_non_empty(self):
        """build_refusal(BUY_SELL) should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_out_of_scope_refusal_is_non_empty(self):
        """build_refusal(OUT_OF_SCOPE) should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_out_of_scope_refusal_contains_amfi_link(self):
        """Out-of-scope refusal must include the AMFI URL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_pii_refusal_is_non_empty(self):
        """build_refusal('pii') should return a non-empty string."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_pii_refusal_does_not_repeat_pii(self):
        """PII refusal must NOT echo back or mention the detected PII value."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_pii_refusal_has_footer(self):
        """PII refusal must include the 'Last updated from sources:' footer."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_no_refusal_gives_investment_advice(self):
        """No refusal response should contain phrases like 'you should invest'."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_invalid_intent_raises_value_error(self):
        """build_refusal() with an unknown intent string should raise ValueError."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

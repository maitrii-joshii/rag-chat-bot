"""
tests/test_guardrails.py — Unit Tests for Guardrail Modules (Phase 3)

Tests:
  - PII detection (all 5 PII types, true/false positive cases)
  - Advisory intent classification
  - Comparison intent classification
  - Prediction intent classification
  - Buy/Sell intent classification
  - Out-of-scope classification
  - Factual queries correctly pass through

Phase 0: Test skeleton with placeholder assertions.
Phase 3: Full test implementation after guardrails are built.
"""

from __future__ import annotations

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# PII Detector Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPiiDetector:
    """Tests for src.guardrails.pii_detector"""

    def test_detects_pan_number(self):
        """A valid PAN number should be detected."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_detects_aadhaar_number(self):
        """A 12-digit Aadhaar number (with spaces) should be detected."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_detects_indian_mobile(self):
        """An Indian mobile number (+91 prefix or bare 10-digit) should be detected."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_detects_email_address(self):
        """A standard email address should be detected."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_detects_bank_account(self):
        """A 9–18 digit bank account number should be detected."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_clean_query_has_no_pii(self):
        """A normal factual question should return no PII matches."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_contains_pii_true(self):
        """contains_pii() should return True when PII is present."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_contains_pii_false(self):
        """contains_pii() should return False for a clean query."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")


# ─────────────────────────────────────────────────────────────────────────────
# Intent Classifier Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentClassifier:
    """Tests for src.guardrails.intent_classifier"""

    # Factual
    def test_expense_ratio_is_factual(self):
        """'What is the expense ratio of HDFC Small Cap?' → FACTUAL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_exit_load_is_factual(self):
        """'What is the exit load for HDFC Large Cap?' → FACTUAL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_minimum_sip_is_factual(self):
        """'What is the minimum SIP for HDFC Mid Cap?' → FACTUAL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    # Advisory
    def test_should_i_invest_is_advisory(self):
        """'Should I invest in HDFC Small Cap?' → ADVISORY."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_is_it_a_good_fund_is_advisory(self):
        """'Is HDFC Defence Fund a good investment?' → ADVISORY."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    # Comparison
    def test_which_is_better_is_comparison(self):
        """'Which is better — HDFC Small Cap or Mid Cap?' → COMPARISON."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_compare_is_comparison(self):
        """'Compare HDFC Large Cap and Multi Cap' → COMPARISON."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    # Prediction
    def test_will_it_give_returns_is_prediction(self):
        """'Will HDFC Defence Fund give 20% returns?' → PREDICTION."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_future_performance_is_prediction(self):
        """'What will be the future performance of HDFC Gold?' → PREDICTION."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    # Buy / Sell
    def test_should_i_buy_is_buy_sell(self):
        """'Should I buy HDFC Small Cap now?' → BUY_SELL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_time_to_sell_is_buy_sell(self):
        """'Is it time to sell HDFC Balanced Advantage?' → BUY_SELL."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    # Out of scope
    def test_weather_is_out_of_scope(self):
        """'What is the weather today?' → OUT_OF_SCOPE."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

    def test_unrelated_topic_is_out_of_scope(self):
        """'Who won the cricket match?' → OUT_OF_SCOPE."""
        pytest.skip("Phase 0 stub — implement in Phase 3.")

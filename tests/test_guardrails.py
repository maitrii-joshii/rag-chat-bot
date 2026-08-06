"""
tests/test_guardrails.py -- Unit Tests for Guardrail Modules (Task 3.6)

Covers:
  - PII detection: all 5 types, true/false positives, contains_pii wrapper
  - Advisory intent: 5 phrasings
  - Comparison intent: 4 phrasings
  - Prediction intent: 4 phrasings
  - Buy/Sell intent: 4 phrasings
  - Out-of-scope: 4 non-MF queries
  - Factual pass-through: 6 genuine fund questions
  - is_factual / is_blocked helpers
"""

from __future__ import annotations

import pytest

from src.guardrails.pii_detector import detect_pii, contains_pii
from src.guardrails.intent_classifier import classify, is_factual, is_blocked, QueryIntent


# ─────────────────────────────────────────────────────────────────────────────
# PII Detector Tests (Task 3.1)
# ─────────────────────────────────────────────────────────────────────────────

class TestPiiDetector:
    """Tests for src.guardrails.pii_detector"""

    # ── PAN ──────────────────────────────────────────────────────────────────
    def test_detects_pan_number(self):
        result = detect_pii("My PAN is ABCDE1234F, can you help?")
        assert "pan" in result
        assert "ABCDE1234F" in result["pan"]

    def test_detects_pan_lowercase_query(self):
        result = detect_pii("pan number PQRST5678G")
        assert "pan" in result

    def test_no_false_positive_for_short_alpha(self):
        """5-char strings without the right pattern should NOT match PAN."""
        result = detect_pii("HDFC fund has great returns")
        assert "pan" not in result

    # ── Aadhaar ──────────────────────────────────────────────────────────────
    def test_detects_aadhaar_number(self):
        result = detect_pii("My Aadhaar is 1234 5678 9012")
        assert "aadhaar" in result

    def test_detects_aadhaar_without_spaces(self):
        result = detect_pii("Aadhaar: 123456789012")
        assert "aadhaar" in result

    def test_aadhaar_false_positive_isin_suppressed(self):
        """A 12-digit ISIN-adjacent number should NOT trigger aadhaar."""
        result = detect_pii("ISIN: 123456789012")
        assert "aadhaar" not in result

    # ── Phone ─────────────────────────────────────────────────────────────────
    def test_detects_indian_mobile(self):
        result = detect_pii("Call me on 9876543210")
        assert "phone" in result

    def test_detects_mobile_with_plus91(self):
        result = detect_pii("My number is +919876543210")
        assert "phone" in result

    def test_no_false_positive_short_number(self):
        """A 6-digit number should NOT match phone."""
        result = detect_pii("NAV is 123456")
        assert "phone" not in result

    # ── Email ─────────────────────────────────────────────────────────────────
    def test_detects_email_address(self):
        result = detect_pii("Contact me at user@example.com")
        assert "email" in result

    def test_detects_email_with_dots(self):
        result = detect_pii("My email: first.last@company.co.in")
        assert "email" in result

    def test_no_false_positive_plain_url(self):
        """A plain URL without @ should NOT match email."""
        result = detect_pii("Visit https://www.amfiindia.com for details")
        assert "email" not in result

    # ── Bank Account ──────────────────────────────────────────────────────────
    def test_detects_bank_account(self):
        result = detect_pii("My account no: 123456789012")
        assert "bank_account" in result

    def test_detects_bank_account_with_a_c(self):
        result = detect_pii("a/c no 987654321098")
        assert "bank_account" in result

    def test_no_false_positive_nav_value(self):
        """A large NAV figure without account keyword should NOT match bank_account."""
        result = detect_pii("NAV is 12345678901")
        assert "bank_account" not in result

    # ── contains_pii wrapper ──────────────────────────────────────────────────
    def test_contains_pii_true(self):
        assert contains_pii("My PAN is ABCDE1234F") is True

    def test_contains_pii_false(self):
        assert contains_pii("What is the expense ratio of HDFC Small Cap?") is False

    def test_clean_query_has_no_pii(self):
        result = detect_pii("What is the exit load for HDFC Defence Fund?")
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# Intent Classifier Tests (Tasks 3.2 & 3.3)
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentClassifier:
    """Tests for src.guardrails.intent_classifier"""

    # ── Factual (should proceed to RAG) ───────────────────────────────────────
    def test_expense_ratio_is_factual(self):
        assert classify("What is the expense ratio of HDFC Small Cap?") == QueryIntent.FACTUAL

    def test_exit_load_is_factual(self):
        assert classify("What is the exit load for HDFC Large Cap?") == QueryIntent.FACTUAL

    def test_minimum_sip_is_factual(self):
        assert classify("What is the minimum SIP for HDFC Mid Cap fund?") == QueryIntent.FACTUAL

    def test_nav_question_is_factual(self):
        assert classify("What is the NAV of HDFC Gold ETF?") == QueryIntent.FACTUAL

    def test_fund_manager_is_factual(self):
        assert classify("Who manages the HDFC Defence fund?") == QueryIntent.FACTUAL

    def test_category_question_is_factual(self):
        assert classify("What category does HDFC Balanced Advantage belong to?") == QueryIntent.FACTUAL

    # ── Advisory ──────────────────────────────────────────────────────────────
    def test_should_i_invest_is_advisory(self):
        assert classify("Should I invest in HDFC Small Cap?") == QueryIntent.ADVISORY

    def test_is_it_a_good_fund_is_advisory(self):
        assert classify("Is HDFC Defence Fund a good investment?") == QueryIntent.ADVISORY

    def test_recommend_fund_is_advisory(self):
        assert classify("Can you recommend a fund for me?") == QueryIntent.ADVISORY

    def test_worth_investing_is_advisory(self):
        assert classify("Is HDFC Gold ETF worth investing?") == QueryIntent.ADVISORY

    def test_advise_me_is_advisory(self):
        assert classify("Advise me on the best HDFC fund") == QueryIntent.ADVISORY

    # ── Comparison ────────────────────────────────────────────────────────────
    def test_which_is_better_is_comparison(self):
        assert classify("Which is better — HDFC Small Cap or Mid Cap?") == QueryIntent.COMPARISON

    def test_compare_is_comparison(self):
        assert classify("Compare HDFC Large Cap and Multi Cap") == QueryIntent.COMPARISON

    def test_vs_is_comparison(self):
        assert classify("HDFC Small Cap vs HDFC Mid Cap") == QueryIntent.COMPARISON

    def test_better_than_is_comparison(self):
        assert classify("Is HDFC Small Cap better than Nifty Next 50?") == QueryIntent.COMPARISON

    # ── Prediction ────────────────────────────────────────────────────────────
    def test_will_it_give_returns_is_prediction(self):
        assert classify("Will HDFC Defence Fund give 20% returns?") == QueryIntent.PREDICTION

    def test_future_performance_is_prediction(self):
        assert classify("What will be the future performance of HDFC Gold?") == QueryIntent.PREDICTION

    def test_expected_returns_is_prediction(self):
        assert classify("What are the expected returns of HDFC Small Cap?") == QueryIntent.PREDICTION

    def test_forecast_is_prediction(self):
        assert classify("Forecast for HDFC Balanced Advantage fund") == QueryIntent.PREDICTION

    # ── Buy / Sell ────────────────────────────────────────────────────────────
    def test_should_i_buy_is_buy_sell(self):
        assert classify("Should I buy HDFC Small Cap now?") == QueryIntent.BUY_SELL

    def test_time_to_sell_is_buy_sell(self):
        assert classify("Is it time to sell HDFC Balanced Advantage?") == QueryIntent.BUY_SELL

    def test_when_to_redeem_is_buy_sell(self):
        assert classify("When should I redeem HDFC Mid Cap?") == QueryIntent.BUY_SELL

    def test_should_i_exit_is_buy_sell(self):
        assert classify("Should I exit HDFC Defence fund?") == QueryIntent.BUY_SELL

    # ── Out of Scope (Task 3.3) ───────────────────────────────────────────────
    def test_weather_is_out_of_scope(self):
        assert classify("What is the weather today?") == QueryIntent.OUT_OF_SCOPE

    def test_cricket_is_out_of_scope(self):
        assert classify("Who won the cricket match?") == QueryIntent.OUT_OF_SCOPE

    def test_recipe_is_out_of_scope(self):
        assert classify("How do I make biryani?") == QueryIntent.OUT_OF_SCOPE

    def test_stock_price_is_out_of_scope(self):
        assert classify("What is the share price of Reliance?") == QueryIntent.OUT_OF_SCOPE

    # ── Helpers ───────────────────────────────────────────────────────────────
    def test_is_factual_true(self):
        assert is_factual("What is the expense ratio of HDFC Small Cap?") is True

    def test_is_factual_false_for_advisory(self):
        assert is_factual("Should I invest in HDFC Gold?") is False

    def test_is_blocked_true_for_advisory(self):
        assert is_blocked("Should I invest in HDFC Small Cap?") is True

    def test_is_blocked_false_for_factual(self):
        assert is_blocked("What is the NAV of HDFC Defence Fund?") is False

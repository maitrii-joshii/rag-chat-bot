"""
Guardrails -- PII Detector (Task 3.1)

Regex-based detection of Personally Identifiable Information (PII) in user
queries. Detected PII is NEVER logged or stored -- the query is blocked before
reaching the RAG pipeline.

Detected PII types (§8.3):
  - PAN card number      : AAAAA9999A (5 alpha, 4 digit, 1 alpha)
  - Aadhaar number       : 12 digits, optional spaces every 4 digits
  - Indian mobile phone  : (+91 optional) followed by [6-9] + 9 digits
  - Email address        : RFC 5322 simplified pattern
  - Bank account number  : 9-18 digits with context keyword guard to
                           avoid false positives on monetary figures

Architecture reference: §8.3 PII Detection Patterns (Regex)
"""

from __future__ import annotations

import re

# ── PII Regex Patterns (Task 3.1) ─────────────────────────────────────────────

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    # PAN: AAAAA9999A  (exactly 10 chars: 5 alpha, 4 digit, 1 alpha)
    "pan": re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    ),
    # Aadhaar: 12 digits with optional spaces after every 4 digits.
    # Negative lookbehind for '+' to avoid matching the digit-suffix of +91 phone numbers.
    "aadhaar": re.compile(
        r"(?<!\+)(?<!\d)[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}(?!\d)"
    ),
    # Indian mobile: two alternatives:
    #   1. Explicit +91/0091/0 prefix directly followed by [6-9]+9 digits
    #   2. Bare 10-digit number starting with 6-9 (no adjacent digits)
    "phone": re.compile(
        r"(?:\+91|0091|0)\s*[-\.\s]?[6-9][0-9]{9}\b"
        r"|(?<!\d)[6-9][0-9]{9}(?!\d)"
    ),
    # Email: simplified RFC 5322
    "email": re.compile(
        r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
    ),
    # Bank account: 9-18 digits preceded by account-related context keywords.
    # Uses a two-step approach: keyword nearby + digit sequence.
    "bank_account": re.compile(
        r"(?i)(?:account\s*(?:no|num|number)?|a/?c\s*(?:no|num)?|acc(?:ount)?\s*(?:no|num)?)"
        r"\s*[:\-]?\s*"
        r"([0-9]{9,18})\b"
    ),
}

# Aadhaar false-positive guard: 12-digit sequences that are common non-PII
# numbers (e.g., ISINs, timestamps, large monetary figures in paise)
_AADHAAR_FALSE_POSITIVE_CONTEXTS: re.Pattern[str] = re.compile(
    r"(?i)(?:isin|folio|transaction|order|pin\s*code|timestamp|amount|rs\.?|inr)\s*:?\s*[0-9\s]{12}",
)


def detect_pii(text: str) -> dict[str, list[str]]:
    """Scan text for PII and return matches grouped by type.

    Args:
        text: User query or any free-form text to inspect.

    Returns:
        Dict mapping PII type -> list of matched strings.
        Empty dict means no PII detected.

    Note:
        - Aadhaar detection applies a false-positive guard against ISIN codes,
          folio numbers, and large monetary figures.
        - Bank account uses a context keyword requirement to reduce false hits
          on NAV values, timestamps, or return percentages.
        - PII values are returned as-found for audit logging at INFO level,
          but MUST NOT be stored or logged at WARNING/ERROR level.
    """
    results: dict[str, list[str]] = {}

    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type == "bank_account":
            # Bank account uses a capturing group (group 1 = the account number)
            matches = [m.group(1) for m in pattern.finditer(text)]
        else:
            matches = pattern.findall(text)

        if pii_type == "aadhaar" and matches:
            # Remove false positives that appear near context keywords
            # that indicate a non-PII number
            if _AADHAAR_FALSE_POSITIVE_CONTEXTS.search(text):
                matches = []

        if matches:
            results[pii_type] = matches

    return results


def contains_pii(text: str) -> bool:
    """Return True if any PII is detected in the text.

    Convenience wrapper around detect_pii() for use in the guardrail pipeline.

    Args:
        text: Raw user query string.

    Returns:
        True if at least one PII pattern matches, False otherwise.
    """
    return bool(detect_pii(text))

"""
Generation — Response Post-processor (Phase 2 / Phase 3 implementation)

Responsibilities (Phase 2):
  1. Validate response length (≤ 3 sentences).
  2. Verify exactly 1 citation URL is present.
  3. Verify "Last updated" footer is present.

Additional responsibilities (Phase 3):
  4. Scan LLM output for advisory language — reject if detected.
  5. Ensure no PII slipped into the response.

Phase 0: Stub — raises NotImplementedError.
Phase 2 / Phase 3: Full implementation.
"""

from __future__ import annotations


def validate_response(response: str) -> str:
    """Validate and sanitise the raw LLM response.

    Checks enforced:
      - ≤ 3 sentences in the answer body.
      - Exactly 1 ``[Source: <url>]`` citation present.
      - ``Last updated from sources:`` footer present.
      - No advisory language detected (Phase 3 extension).

    Args:
        response: Raw string returned by the Groq LLM.

    Returns:
        The validated (and potentially lightly corrected) response string.

    Raises:
        ValueError: If the response fails validation and cannot be corrected.
        NotImplementedError: Phase 0 stub — implemented in Phase 2.
    """
    raise NotImplementedError(
        "postprocessor.validate_response is a Phase 0 stub. Full implementation in Phase 2."
    )

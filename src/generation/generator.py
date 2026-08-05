"""
Generation -- Groq LLM Generator (Tasks 2.6 & 2.8)

Task 2.6 -- Generator:
  Calls the Groq API with llama-3.1-8b-instant at temperature=0.1,
  max_tokens=150. Sends SYSTEM_PROMPT + build_context_prompt() as the
  message pair.

Task 2.8 -- "No Information" Fallback:
  When the retriever returns no chunks (nothing passes the 0.65 threshold),
  generate() returns the NO_INFORMATION_RESPONSE constant immediately without
  calling the Groq API -- saving latency and tokens.

Architecture reference: §3.6 Generator (LLM), §6.3 Relevance Threshold
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.ingestion.loader import Document
from src.generation.prompts import SYSTEM_PROMPT, build_context_prompt

logger = logging.getLogger(__name__)

# ── LLM Configuration ─────────────────────────────────────────────────────────
DEFAULT_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
DEFAULT_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
DEFAULT_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "150"))

# ── Task 2.8: No-Information Fallback ─────────────────────────────────────────
# Returned immediately when no chunks pass the retrieval threshold.
# No Groq API call is made in this path -- zero LLM cost.
NO_INFORMATION_RESPONSE: str = (
    "I don't have that information in my current knowledge base. "
    "Please visit https://www.amfiindia.com for authoritative fund details. "
    "Last updated from sources: N/A"
)

# Module-level Groq client cache -- created once per process.
_groq_client_cache: dict[str, Any] = {}


def generate(
    query: str,
    chunks: list[Document],
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Generate a factual answer for the given query using retrieved context.

    Args:
        query:       User's natural-language question (after guardrail checks).
        chunks:      Retrieved chunks from the retriever. Empty list triggers
                     the no-information fallback (Task 2.8) immediately.
        model:       Groq model ID (default: llama-3.1-8b-instant).
        temperature: LLM temperature (default: 0.1 for deterministic output).
        max_tokens:  Maximum output tokens (default: 150 for <= 3 sentences).

    Returns:
        LLM-generated answer string, validated by postprocessor.validate_response().
        Returns NO_INFORMATION_RESPONSE when chunks is empty.

    Raises:
        RuntimeError: If the Groq API call fails after the configured retries.
        EnvironmentError: If GROQ_API_KEY is not set.
    """
    # Task 2.8: No-information fallback -- no API call needed.
    if not chunks:
        logger.info("No chunks available -- returning no-information fallback.")
        return NO_INFORMATION_RESPONSE

    # Task 2.6: Build prompt and call Groq API.
    user_prompt = build_context_prompt(query=query, chunks=chunks)

    client = _get_groq_client()

    logger.debug(
        "Calling Groq API: model=%s, temperature=%s, max_tokens=%d",
        model, temperature, max_tokens,
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.error("Groq API call failed: %s", exc)
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    raw_response: str = completion.choices[0].message.content or ""
    logger.debug("Raw LLM response (%d chars): %r", len(raw_response), raw_response[:120])

    # Post-process and validate the response
    from src.generation.postprocessor import validate_response
    validated = validate_response(raw_response)

    return validated


# ── Groq Client Factory ───────────────────────────────────────────────────────

def _get_groq_client() -> Any:
    """Return a cached Groq client, creating it on first call.

    Raises:
        EnvironmentError: If GROQ_API_KEY environment variable is not set.
    """
    cache_key = "default"
    if cache_key not in _groq_client_cache:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Add it to your .env file and restart the application."
            )
        try:
            from groq import Groq
            _groq_client_cache[cache_key] = Groq(api_key=api_key)
            logger.info("Groq client initialised (model: %s)", DEFAULT_MODEL)
        except ImportError as exc:
            raise ImportError(
                "The 'groq' package is not installed. Run: pip install groq"
            ) from exc

    return _groq_client_cache[cache_key]

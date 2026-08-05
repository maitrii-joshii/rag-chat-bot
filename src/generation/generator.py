"""
Generation — Groq LLM Generator (Phase 2 implementation)

Responsibilities:
  1. Accept user query + retrieved chunks.
  2. Assemble prompt using prompts.build_context_prompt().
  3. Call Groq API (llama-3.1-8b-instant, temp=0.1, max_tokens=150).
  4. Return the raw LLM response string.
  5. Handle the "no relevant chunks" fallback path gracefully.

Phase 0: Stub — raises NotImplementedError.
Phase 2: Full implementation.
"""

from __future__ import annotations

from src.ingestion.loader import Document

# ── LLM configuration ─────────────────────────────────────────────────────────
DEFAULT_MODEL: str = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE: float = 0.1
DEFAULT_MAX_TOKENS: int = 150

# ── Fallback response ──────────────────────────────────────────────────────────
NO_INFORMATION_RESPONSE: str = (
    "I don't have that information in my current knowledge base. "
    "Please visit https://www.amfiindia.com for authoritative fund details. "
    "Last updated from sources: N/A"
)


def generate(query: str, chunks: list[Document]) -> str:
    """Generate a factual answer for the given query using retrieved context.

    Args:
        query:  User's natural-language question (after guardrail checks pass).
        chunks: Relevant chunks from the retriever (may be empty list).

    Returns:
        LLM-generated answer string. Returns NO_INFORMATION_RESPONSE when
        ``chunks`` is empty (no relevant context found).

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 2.
    """
    if not chunks:
        return NO_INFORMATION_RESPONSE
    raise NotImplementedError(
        "generator.generate is a Phase 0 stub. Full implementation in Phase 2."
    )

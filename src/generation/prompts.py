"""
Generation — System Prompt & Context Assembly Templates (Phase 2 implementation)

Contains:
  - SYSTEM_PROMPT : Immutable instruction set sent to the Groq LLM on every call.
  - build_context_prompt(): Assembles the final prompt from retrieved chunks + query.

Phase 0: Constants and function signatures defined.
Phase 2: build_context_prompt() fully implemented.
"""

from __future__ import annotations

from src.ingestion.loader import Document

# ── System Prompt ─────────────────────────────────────────────────────────────
# This prompt is immutable — do NOT modify without reviewing Phase 3 guardrails.
SYSTEM_PROMPT: str = """You are a facts-only mutual fund FAQ assistant for HDFC Mutual Fund schemes.
You answer ONLY using the provided context. You MUST follow these rules:

1. Respond in ≤ 3 sentences using only information from the context provided.
2. Include exactly 1 source citation URL from the context metadata (format: [Source: <url>]).
3. End your response with: "Last updated from sources: <fetch_date>"
4. REFUSE any advisory, comparative, or speculative questions politely.
5. NEVER provide investment advice, performance comparisons, or opinions.
6. If the context does not contain the answer, say:
   "I don't have that information in my current knowledge base. Please visit
   https://www.amfiindia.com for authoritative fund details."
"""

# ── Prompt Template ───────────────────────────────────────────────────────────
_CONTEXT_TEMPLATE: str = """### Retrieved Context

{context_blocks}

### User Question

{query}

### Instructions

Answer the question using only the context above. Follow the system rules exactly.
"""


def build_context_prompt(query: str, chunks: list[Document]) -> str:
    """Assemble the user-turn prompt from retrieved chunks and the user query.

    Args:
        query:  The user's natural-language question.
        chunks: Relevant chunks returned by the retriever.

    Returns:
        Formatted prompt string ready to send as the user turn to the LLM.

    Raises:
        NotImplementedError: Phase 0 stub — implemented in Phase 2.
    """
    raise NotImplementedError(
        "prompts.build_context_prompt is a Phase 0 stub. Full implementation in Phase 2."
    )

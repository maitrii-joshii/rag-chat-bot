"""
Generation -- System Prompt & Context Assembly Templates (Tasks 2.4 & 2.5)

Task 2.4 -- System Prompt:
  Immutable facts-only instruction set sent to the Groq LLM on every call.
  Defines response format rules: sentence limit, citation format, footer,
  refusal behaviour, and no-information fallback.

Task 2.5 -- Prompt Template:
  build_context_prompt() assembles the user-turn message by formatting
  retrieved chunks into numbered context blocks with source metadata,
  then appending the user's question and instructions.

Architecture reference: §3.6 Generator (LLM)
"""

from __future__ import annotations

from src.ingestion.loader import Document

# ── Task 2.4: System Prompt ───────────────────────────────────────────────────
# IMMUTABLE — do NOT modify without reviewing Phase 3 guardrails.
# This exact wording is tested in tests/test_refusal.py.
SYSTEM_PROMPT: str = """You are a facts-only mutual fund FAQ assistant for HDFC Mutual Fund schemes.
You answer ONLY using the provided context. You MUST follow these rules strictly:

1. Respond in 1-3 sentences using ONLY information from the context provided.
2. Include exactly 1 source citation URL in this format: [Source: <url>]
3. End your response with exactly this footer: "Last updated from sources: <fetch_date>"
   Use the fetch_date from the context metadata.
4. REFUSE any advisory, comparative, or speculative questions politely.
5. NEVER provide investment advice, performance comparisons, return projections, or opinions.
6. If the context does not contain the answer, respond with exactly:
   "I don't have that information in my current knowledge base. Please visit \
https://www.amfiindia.com for authoritative fund details. Last updated from sources: N/A"

DO NOT make up any facts. DO NOT hallucinate figures or dates not present in the context."""


# ── Task 2.5: Context Block Template ─────────────────────────────────────────
_CHUNK_BLOCK_TEMPLATE: str = """\
[Chunk {index}]
Scheme     : {scheme_name}
Source URL : {source_url}
Fetch Date : {fetch_date}
---
{chunk_text}
"""

_CONTEXT_WRAPPER: str = """\
### Retrieved Context

{context_blocks}
### User Question

{query}

### Instructions

Answer the question using ONLY the context above. Follow all system rules exactly.
Do NOT use knowledge outside the context. If the answer is not in the context, say so.
"""


def build_context_prompt(query: str, chunks: list[Document]) -> str:
    """Assemble the user-turn prompt from retrieved chunks and the user query.

    Each chunk is formatted with its source metadata (scheme name, URL,
    fetch date) and numbered sequentially so the LLM can cite the correct URL.

    Args:
        query:  The user's natural-language question (normalised).
        chunks: Relevant chunk Documents from the retriever.
                If empty, the caller should use NO_INFORMATION_RESPONSE directly
                rather than calling this function.

    Returns:
        Formatted user-turn prompt string ready to send to the Groq LLM.
        Returns a no-context prompt string if chunks is empty (safeguard).
    """
    if not chunks:
        return _CONTEXT_WRAPPER.format(
            context_blocks="[No relevant context found in the knowledge base.]\n\n",
            query=query,
        )

    # Build numbered context blocks from chunks
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata
        block = _CHUNK_BLOCK_TEMPLATE.format(
            index=i,
            scheme_name=meta.get("scheme_name", "Unknown"),
            source_url=meta.get("source_url", "N/A"),
            fetch_date=meta.get("fetch_date", "N/A"),
            chunk_text=chunk.text.strip(),
        )
        blocks.append(block)

    context_blocks = "\n".join(blocks) + "\n"
    return _CONTEXT_WRAPPER.format(context_blocks=context_blocks, query=query)


def format_citation(chunk: Document) -> dict[str, str]:
    """Extract citation metadata from the highest-scoring chunk.

    Used by the API response schema to return structured citation data.

    Args:
        chunk: The top-scoring Document from the retriever.

    Returns:
        Dict with keys: url, scheme_name, fetch_date.
    """
    meta = chunk.metadata
    return {
        "url": meta.get("source_url", ""),
        "scheme_name": meta.get("scheme_name", ""),
        "fetch_date": meta.get("fetch_date", "N/A"),
    }

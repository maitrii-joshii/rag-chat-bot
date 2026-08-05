"""
API — Pydantic Schemas (Phase 4 implementation)

Request / response models for:
  - POST /api/chat
  - GET  /api/health
  - GET  /api/examples

Phase 0: Model definitions as stubs (fields declared, no validators).
Phase 4: Full implementation with validators and documentation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── /api/chat ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user's factual question about an HDFC Mutual Fund scheme.",
        examples=["What is the expense ratio of HDFC Small Cap Fund?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional client-generated session identifier for logging.",
    )


class CitationModel(BaseModel):
    """Embedded citation metadata in a chat response."""

    url: str = Field(..., description="Source URL from the retrieved chunk metadata.")
    scheme_name: str = Field(..., description="Human-readable scheme name.")
    fetch_date: str = Field(..., description="ISO-8601 date when the source was last fetched.")


class ChatResponse(BaseModel):
    """Response body for POST /api/chat."""

    answer: str = Field(..., description="Factual answer (≤ 3 sentences).")
    citation: CitationModel | None = Field(
        default=None,
        description="Source citation — None when answering with a refusal.",
    )
    last_updated: str = Field(..., description="ISO-8601 timestamp of the source fetch date.")
    query_type: str = Field(
        ...,
        description=(
            "Intent classification result: factual | advisory | comparison | "
            "prediction | buy_sell | out_of_scope | pii_blocked"
        ),
    )


# ── /api/health ───────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response body for GET /api/health."""

    status: str = Field(..., description="'healthy' or 'degraded'.")
    vectorstore_chunks: int = Field(
        ..., description="Number of chunks currently stored in ChromaDB."
    )
    model: str = Field(..., description="LLM model in use.")
    embedding_model: str = Field(..., description="Embedding model in use.")


# ── /api/examples ─────────────────────────────────────────────────────────────

class ExamplesResponse(BaseModel):
    """Response body for GET /api/examples."""

    examples: list[str] = Field(
        ...,
        description="List of 3 clickable example questions for the UI.",
        examples=[
            [
                "What is the expense ratio of HDFC Small Cap Fund?",
                "What is the exit load for HDFC Large Cap Fund?",
                "What is the minimum SIP for HDFC Mid Cap Fund?",
            ]
        ],
    )

"""
API -- Pydantic Schemas (Task 4.1)

Request / response models for:
  - POST /api/chat
  - GET  /api/health
  - GET  /api/examples

Validators added in Phase 4:
  - ChatRequest.query: strip whitespace, reject empty after strip, cap length
  - ChatRequest.session_id: strip whitespace if provided
  - ChatResponse: query_type constrained to known values

Architecture reference: §9.1 API Endpoints
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ── /api/chat Request ─────────────────────────────────────────────────────────

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

    @field_validator("query", mode="before")
    @classmethod
    def strip_and_validate_query(cls, v: str) -> str:
        """Strip whitespace and reject blank queries."""
        if not isinstance(v, str):
            raise ValueError("query must be a string.")
        v = v.strip()
        if not v:
            raise ValueError("query must not be blank or whitespace-only.")
        return v

    @field_validator("session_id", mode="before")
    @classmethod
    def strip_session_id(cls, v: str | None) -> str | None:
        """Strip whitespace from session_id if provided."""
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        return v


# ── /api/chat Response ────────────────────────────────────────────────────────

# All valid query_type values (mirrors QueryIntent enum + "pii_blocked")
VALID_QUERY_TYPES: frozenset[str] = frozenset(
    {"factual", "advisory", "comparison", "prediction", "buy_sell", "out_of_scope", "pii_blocked", "greeting"}
)


class CitationModel(BaseModel):
    """Embedded citation metadata in a chat response."""

    url: str = Field(..., description="Source URL from the retrieved chunk metadata.")
    scheme_name: str = Field(..., description="Human-readable scheme name.")
    fetch_date: str = Field(..., description="ISO-8601 date when the source was last fetched.")


class ChatResponse(BaseModel):
    """Response body for POST /api/chat."""

    answer: str = Field(..., description="Factual answer (<=3 sentences) or refusal message.")
    citation: CitationModel | None = Field(
        default=None,
        description="Source citation. None for refusals and no-information responses.",
    )
    last_updated: str = Field(
        ...,
        description="Fetch date from source metadata, or 'N/A' for non-factual responses.",
    )
    query_type: str = Field(
        ...,
        description=(
            "Intent classification: factual | advisory | comparison | "
            "prediction | buy_sell | out_of_scope | pii_blocked | greeting"
        ),
    )

    @field_validator("query_type")
    @classmethod
    def validate_query_type(cls, v: str) -> str:
        if v not in VALID_QUERY_TYPES:
            raise ValueError(
                f"query_type must be one of {sorted(VALID_QUERY_TYPES)}, got {v!r}"
            )
        return v


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
        description="List of 3 clickable example questions for the chat UI.",
        examples=[
            [
                "What is the expense ratio of HDFC Small Cap Fund?",
                "What is the exit load for HDFC Large Cap Fund?",
                "What is the minimum SIP for HDFC Mid Cap Fund?",
            ]
        ],
    )

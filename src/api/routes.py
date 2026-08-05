"""
API — FastAPI Route Definitions (Phase 4 implementation)

Endpoints:
  POST /api/chat     — Main Q&A endpoint (guardrails → retriever → generator)
  GET  /api/health   — Health check with ChromaDB chunk count
  GET  /api/examples — Returns 3 example questions for the UI

Phase 0: Route stubs that return placeholder responses.
Phase 4: Full orchestration wired in.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import ChatRequest, ChatResponse, ExamplesResponse, HealthResponse

router = APIRouter(prefix="/api")

# ── Example questions (updated in Phase 4 with production-ready queries) ──────
_EXAMPLE_QUESTIONS: list[str] = [
    "What is the expense ratio of HDFC Small Cap Fund?",
    "What is the exit load for HDFC Large Cap Fund?",
    "What is the minimum SIP amount for HDFC Mid Cap Fund?",
]


@router.post("/chat", response_model=ChatResponse, summary="Submit a factual Q&A query")
async def chat(request: ChatRequest) -> ChatResponse:
    """Accept a user query, run it through the RAG pipeline, and return an answer.

    Phase 0 stub — returns a placeholder response.
    Phase 4 will wire: guardrails → retriever → generator → postprocessor.
    """
    # Phase 0 placeholder
    return ChatResponse(
        answer="Phase 0 scaffold — RAG pipeline not yet implemented.",
        citation=None,
        last_updated="N/A",
        query_type="factual",
    )


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health() -> HealthResponse:
    """Return service health status and ChromaDB chunk count.

    Phase 0 stub — vectorstore_chunks is 0 until Phase 1 populates the store.
    """
    return HealthResponse(
        status="healthy",
        vectorstore_chunks=0,
        model="llama-3.1-8b-instant",
        embedding_model="BAAI/bge-small-en-v1.5",
    )


@router.get("/examples", response_model=ExamplesResponse, summary="Return example questions")
async def examples() -> ExamplesResponse:
    """Return a list of example factual questions for the chat UI."""
    return ExamplesResponse(examples=_EXAMPLE_QUESTIONS)

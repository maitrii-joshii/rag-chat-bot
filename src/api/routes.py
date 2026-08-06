"""
API -- FastAPI Route Definitions (Tasks 4.2 & 4.4)

Task 4.2 -- API Routes:
  POST /api/chat     -- Main Q&A endpoint
  GET  /api/health   -- Health check with ChromaDB chunk count
  GET  /api/examples -- Returns 3 example questions for the UI

Task 4.4 -- Chat Orchestrator:
  Wires the full pipeline for POST /api/chat:
    1. PII check (pii_detector)         -- block if PII detected
    2. Intent classify (intent_classifier) -- refuse if not FACTUAL
    3. Retrieve chunks (retriever)       -- embed + vector search
    4. Generate answer (generator)       -- Groq LLM call
    5. Extract citation (postprocessor)  -- parse [Source: url] and footer
    6. Return ChatResponse

Architecture references: §9.1 API Endpoints, §10.2 Query Flow (Online)
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request

from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationModel,
    ExamplesResponse,
    HealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# ── Configuration ──────────────────────────────────────────────────────────────
_VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "./data/vectorstore")
_COLLECTION_NAME  = os.getenv("VECTORSTORE_COLLECTION", "mf_faq_v1")

# ── Example questions shown in the chat UI ─────────────────────────────────────
_EXAMPLE_QUESTIONS: list[str] = [
    "What is the expense ratio of HDFC Small Cap Fund?",
    "What is the exit load for HDFC Large Cap Fund?",
    "What is the minimum SIP amount for HDFC Mid Cap Fund?",
]


# ── POST /api/chat (Tasks 4.2 + 4.4) ──────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Submit a factual Q&A query",
    description=(
        "Accepts a natural-language question about HDFC Mutual Fund schemes. "
        "Runs the query through guardrails, retrieval, and generation. "
        "Returns a factual answer with source citation, or a polite refusal."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Full chat orchestrator: guardrails → retrieval → generation.

    Args:
        request: Validated ChatRequest with query and optional session_id.

    Returns:
        ChatResponse with answer, citation, last_updated, and query_type.

    Raises:
        HTTPException 429: Rate limit exceeded (handled in main.py middleware).
        HTTPException 500: Unexpected pipeline error.
    """
    query = request.query
    session_id = request.session_id or "anonymous"

    logger.info("Chat request | session=%s | query=%r", session_id, query[:80])

    # ── Step 1: PII Detection ─────────────────────────────────────────────────
    from src.guardrails.pii_detector import contains_pii
    if contains_pii(query):
        logger.warning("PII detected in query | session=%s", session_id)
        from src.guardrails.refusal_handler import build_refusal
        return ChatResponse(
            answer=build_refusal("pii"),
            citation=None,
            last_updated="N/A",
            query_type="pii_blocked",
        )

    # ── Step 2: Intent Classification ─────────────────────────────────────────
    from src.guardrails.intent_classifier import classify, QueryIntent
    intent = classify(query)
    logger.debug("Intent classified: %s | session=%s", intent.value, session_id)

    if intent != QueryIntent.FACTUAL:
        from src.guardrails.refusal_handler import build_refusal
        logger.info("Refusing %s query | session=%s", intent.value, session_id)
        return ChatResponse(
            answer=build_refusal(intent),
            citation=None,
            last_updated="N/A",
            query_type=intent.value,
        )

    # ── Step 3: Retrieval ─────────────────────────────────────────────────────
    from src.retrieval.retriever import retrieve
    try:
        chunks = retrieve(query, vectorstore_path=_VECTORSTORE_PATH)
    except Exception as exc:
        logger.error("Retrieval failed: %s | session=%s", exc, session_id)
        raise HTTPException(status_code=500, detail="Retrieval pipeline error.") from exc

    logger.debug("Retrieved %d chunks | session=%s", len(chunks), session_id)

    # ── Step 4: Generation ────────────────────────────────────────────────────
    from src.generation.generator import generate, NO_INFORMATION_RESPONSE
    try:
        answer = generate(query, chunks)
    except EnvironmentError as exc:
        logger.error("Groq API key missing: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable — GROQ_API_KEY not configured.",
        ) from exc
    except ValueError as exc:
        # Post-generation validation failed (advisory language or PII in output)
        logger.error("Post-generation validation failed: %s | session=%s", exc, session_id)
        from src.generation.generator import NO_INFORMATION_RESPONSE as _FALLBACK
        answer = _FALLBACK
        chunks = []  # No citation for validation-failed responses
    except Exception as exc:
        logger.error("Generation failed: %s | session=%s", exc, session_id)
        raise HTTPException(status_code=500, detail="Generation pipeline error.") from exc

    # ── Step 5: Extract citation and last_updated ─────────────────────────────
    citation: CitationModel | None = None
    last_updated = "N/A"

    if chunks:
        from src.generation.prompts import format_citation
        from src.generation.postprocessor import extract_last_updated
        top_chunk = chunks[0]
        cite_data = format_citation(top_chunk)
        if cite_data.get("url"):
            citation = CitationModel(
                url=cite_data["url"],
                scheme_name=cite_data.get("scheme_name", ""),
                fetch_date=cite_data.get("fetch_date", "N/A"),
            )
        last_updated = extract_last_updated(answer) or cite_data.get("fetch_date", "N/A")

    logger.info(
        "Chat response | session=%s | query_type=factual | chunks=%d | citation=%s",
        session_id, len(chunks), citation.url if citation else "none",
    )

    return ChatResponse(
        answer=answer,
        citation=citation,
        last_updated=last_updated,
        query_type="factual",
    )


# ── GET /api/health (Task 4.2) ────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description="Returns service status and current ChromaDB chunk count.",
)
async def health() -> HealthResponse:
    """Return service health and vectorstore statistics."""
    chunk_count = 0
    status = "healthy"

    try:
        import chromadb
        client = chromadb.PersistentClient(path=_VECTORSTORE_PATH)
        collection = client.get_collection(name=_COLLECTION_NAME)
        chunk_count = collection.count()
    except Exception as exc:
        logger.warning("Health check: vectorstore unavailable — %s", exc)
        status = "degraded"

    from src.generation.generator import DEFAULT_MODEL
    from src.ingestion.embedder import DEFAULT_EMBEDDING_MODEL

    return HealthResponse(
        status=status,
        vectorstore_chunks=chunk_count,
        model=DEFAULT_MODEL,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
    )


# ── GET /api/examples (Task 4.2) ──────────────────────────────────────────────

@router.get(
    "/examples",
    response_model=ExamplesResponse,
    summary="Return clickable example questions",
    description="Returns 3 example factual questions for display in the chat UI.",
)
async def examples() -> ExamplesResponse:
    """Return example questions for the chat UI."""
    return ExamplesResponse(examples=_EXAMPLE_QUESTIONS)

# ── POST /api/admin/ingest ────────────────────────────────────────────────────

@router.post("/admin/ingest", include_in_schema=False)
async def admin_ingest(background_tasks: BackgroundTasks):
    """Trigger the ingestion pipeline in the background using the loaded model."""
    from scripts.ingest import load_corpus, run_pipeline
    from pathlib import Path
    
    def _run_ingest():
        try:
            corpus_path = Path("data/corpus.yml")
            vectorstore_path = Path(os.getenv("VECTORSTORE_PATH", "data/vectorstore"))
            sources = load_corpus(corpus_path)
            # Disable caching on requests to avoid holding memory
            run_pipeline(sources, vectorstore_path)
            logger.info("Background ingestion completed successfully")
        except Exception as e:
            logger.error("Background ingestion failed: %s", e)
            
    background_tasks.add_task(_run_ingest)
    return {"status": "Ingestion started in background"}

"""
RAG Mutual Fund FAQ Assistant -- FastAPI Application (Tasks 4.3 & 4.5)

Task 4.3 -- FastAPI App:
  - CORS middleware (configurable allowed origins via ALLOWED_ORIGINS env var)
  - Static file serving: GET /  serves src/ui/ (index.html, style.css, script.js)
  - API router mounted at /api
  - Application lifespan: pre-warms BGE embedding model on startup
  - Structured JSON logging in production; coloured logging in development

Task 4.5 -- Rate Limiting:
  - In-memory sliding window rate limiter (no Redis required for MVP)
  - Default: 30 requests / 60 seconds per client IP on POST /api/chat
  - Configurable via RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW_SECONDS env vars
  - Returns HTTP 429 with Retry-After header on breach

Architecture references:
  - §11 Technology Stack
  - §2 High-Level Architecture (API Gateway / Rate Limiting)
"""

from __future__ import annotations

import io
import logging
import os
import sys
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Load .env before any module reads environment variables

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


# ── Encoding fix (Windows compatibility) ──────────────────────────────────────
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )

# ── Logging setup ─────────────────────────────────────────────────────────────
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Configuration (env-overridable) ───────────────────────────────────────────
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

_ALLOWED_ORIGINS_RAW = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,https://rag-chat-bot-lac.vercel.app",
)
_ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in _ALLOWED_ORIGINS_RAW.split(",") if o.strip()
]

# Static UI directory
_UI_DIR = Path(__file__).resolve().parent / "ui"

# Rate limiting config (Task 4.5)
_RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


# ── Task 4.5: In-Memory Sliding Window Rate Limiter ───────────────────────────
# Maps client IP → deque of request timestamps (seconds since epoch).
# Thread-safe enough for asyncio (single-threaded event loop).
_rate_limit_store: dict[str, deque[float]] = defaultdict(
    lambda: deque(maxlen=_RATE_LIMIT_REQUESTS + 1)
)


def _check_rate_limit(client_ip: str) -> tuple[bool, int]:
    """Check if the client has exceeded the rate limit.

    Uses a sliding window: counts requests within the last WINDOW seconds.

    Args:
        client_ip: Client IP address string.

    Returns:
        Tuple (is_allowed: bool, retry_after_seconds: int).
        retry_after_seconds is 0 when is_allowed is True.
    """
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    bucket = _rate_limit_store[client_ip]

    # Evict timestamps outside the window
    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= _RATE_LIMIT_REQUESTS:
        # Calculate when the oldest request will fall outside the window
        retry_after = int(_RATE_LIMIT_WINDOW_SECONDS - (now - bucket[0])) + 1
        return False, retry_after

    bucket.append(now)
    return True, 0


# ── Application Lifespan (startup / shutdown) ─────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm the BGE embedding model on startup so the first request is fast."""
    logger.info("Starting RAG Mutual Fund FAQ Assistant (%s mode)", _ENVIRONMENT)
    logger.info("Allowed CORS origins: %s", _ALLOWED_ORIGINS)

    # Pre-warm BGE model (loads weights into memory)
    try:
        from src.ingestion.embedder import _get_or_load_model, DEFAULT_EMBEDDING_MODEL
        logger.info("Pre-warming embedding model: %s", DEFAULT_EMBEDDING_MODEL)
        _get_or_load_model(DEFAULT_EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully.")
    except Exception as exc:
        logger.warning("Could not pre-warm embedding model: %s", exc)

    # Log vectorstore status
    try:
        import chromadb
        from src.ingestion.embedder import COLLECTION_NAME
        vectorstore_path = os.getenv("VECTORSTORE_PATH", "./data/vectorstore")
        client = chromadb.PersistentClient(path=vectorstore_path)
        col = client.get_collection(name=COLLECTION_NAME)
        logger.info("Vectorstore ready: %d chunks in '%s'", col.count(), COLLECTION_NAME)
    except Exception as exc:
        logger.warning("Vectorstore not ready: %s -- run scripts/ingest.py first", exc)

    yield  # Application runs here

    logger.info("Shutting down RAG Mutual Fund FAQ Assistant.")


# ── FastAPI Application (Task 4.3) ────────────────────────────────────────────

app = FastAPI(
    title="RAG Mutual Fund FAQ Assistant",
    description=(
        "A facts-only Q&A assistant for HDFC Mutual Fund schemes. "
        "Answers are derived exclusively from approved corpus sources via RAG. "
        "No investment advice is provided."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS Middleware (Task 4.3) ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Task 4.5: Rate Limiting Middleware ────────────────────────────────────────
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply sliding-window rate limiting to POST /api/chat only."""
    if request.method == "POST" and request.url.path == "/api/chat":
        client_ip = request.client.host if request.client else "unknown"
        allowed, retry_after = _check_rate_limit(client_ip)
        if not allowed:
            logger.warning(
                "Rate limit exceeded | ip=%s | retry_after=%ds", client_ip, retry_after
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Too many requests. Please wait {retry_after} second(s) "
                        "before trying again."
                    )
                },
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)

# ── API Router (Task 4.3) ─────────────────────────────────────────────────────
from src.api.routes import router as api_router  # noqa: E402
app.include_router(api_router)

# ── Static File Serving (Task 4.3) ────────────────────────────────────────────
# Serve the chat UI at / — must be mounted AFTER routes to avoid shadowing /api
if _UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
    logger.debug("Static UI mounted from: %s", _UI_DIR)
else:
    # Fallback root endpoint when UI hasn't been built yet
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "message": "RAG Mutual Fund FAQ Assistant is running.",
            "docs": "/api/docs",
            "health": "/api/health",
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, workers=1)

"""
RAG Mutual Fund FAQ Assistant — FastAPI Application Entry Point

Phase 4 will fully wire:
  - CORS middleware
  - Static file serving (src/ui/)
  - API routes (/api/chat, /api/health, /api/examples)
  - Rate limiting

For Phase 0 this file is a minimal scaffold so imports resolve.
"""

from fastapi import FastAPI

app = FastAPI(
    title="RAG Mutual Fund FAQ Assistant",
    description=(
        "A facts-only Q&A assistant for HDFC Mutual Fund schemes. "
        "Answers are derived exclusively from approved corpus sources."
    ),
    version="0.1.0",
)


@app.get("/")
async def root() -> dict:
    """Health-check / root redirect — placeholder until Phase 4."""
    return {"message": "RAG Mutual Fund FAQ Assistant is running. See /api/health."}

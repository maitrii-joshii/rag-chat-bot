"""
Retrieval — Retriever (Tasks 2.1, 2.2, 2.3)

Task 2.1 — Retriever:
  - Embed user query with BGE (same model used during ingestion).
  - Apply BGE's recommended query prefix.
  - Search ChromaDB collection 'mf_faq_v1' using cosine similarity.
  - Return top-k chunks with similarity score >= threshold.

Task 2.2 — Query Pre-processing:
  - Lowercase normalisation.
  - Scheme name canonicalisation: informal names ("small cap", "hdfc gold")
    are mapped to the exact ChromaDB scheme_name values used at ingest time.

Task 2.3 — Metadata Pre-filtering:
  - If a canonical scheme name is detected in the query, add a ChromaDB
    `where={"scheme_name": <canonical>}` filter before vector search.
  - Reduces search space and improves precision for fund-specific queries.

Architecture references: §3.5, §6.1, §6.2, §6.3
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from src.ingestion.loader import Document
from src.ingestion.embedder import (
    COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    _get_or_load_model,
)

logger = logging.getLogger(__name__)

# ── Retrieval Configuration ────────────────────────────────────────────────────
DEFAULT_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
DEFAULT_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.65"))
DEFAULT_VECTORSTORE_PATH: str = os.getenv("VECTORSTORE_PATH", "./data/vectorstore")

# BGE recommended query prefix (different from the passage prefix used at index time)
_BGE_QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "

# ── Task 2.2: Scheme Name Canonicalisation Map ────────────────────────────────
# Maps lowercase search terms (substrings found in user queries) to the exact
# scheme_name strings stored in ChromaDB metadata.
# Keys are ordered from most specific to least specific to avoid false matches.
_SCHEME_ALIASES: dict[str, str] = {
    # Small Cap
    "hdfc small cap":           "HDFC Small Cap Fund - Direct Growth",
    "small cap":                "HDFC Small Cap Fund - Direct Growth",

    # Gold
    "hdfc gold etf":            "HDFC Gold ETF Fund of Fund - Direct Plan Growth",
    "gold etf":                 "HDFC Gold ETF Fund of Fund - Direct Plan Growth",
    "gold fund":                "HDFC Gold ETF Fund of Fund - Direct Plan Growth",
    "hdfc gold":                "HDFC Gold ETF Fund of Fund - Direct Plan Growth",

    # Multi Cap
    "hdfc multi cap":           "HDFC Multi Cap Fund - Direct Growth",
    "multi cap":                "HDFC Multi Cap Fund - Direct Growth",
    "multicap":                 "HDFC Multi Cap Fund - Direct Growth",

    # Large Cap
    "hdfc large cap":           "HDFC Large Cap Fund - Direct Growth",
    "large cap":                "HDFC Large Cap Fund - Direct Growth",
    "largecap":                 "HDFC Large Cap Fund - Direct Growth",

    # Mid Cap
    "hdfc mid cap":             "HDFC Mid Cap Fund - Direct Growth",
    "mid cap":                  "HDFC Mid Cap Fund - Direct Growth",
    "midcap":                   "HDFC Mid Cap Fund - Direct Growth",

    # BSE Sensex Index
    "hdfc bse sensex":          "HDFC BSE Sensex Index Fund - Direct Growth",
    "bse sensex":               "HDFC BSE Sensex Index Fund - Direct Growth",
    "sensex index":             "HDFC BSE Sensex Index Fund - Direct Growth",
    "sensex fund":              "HDFC BSE Sensex Index Fund - Direct Growth",

    # Short Term Opportunities
    "hdfc short term":          "HDFC Short Term Opportunities Fund - Direct Growth",
    "short term":               "HDFC Short Term Opportunities Fund - Direct Growth",
    "short duration":           "HDFC Short Term Opportunities Fund - Direct Growth",

    # Focused
    "hdfc focused":             "HDFC Focused Fund - Direct Growth",
    "focused fund":             "HDFC Focused Fund - Direct Growth",

    # Nifty Next 50
    "hdfc nifty next 50":       "HDFC Nifty Next 50 Index Fund - Direct Growth",
    "nifty next 50":            "HDFC Nifty Next 50 Index Fund - Direct Growth",
    "nifty next50":             "HDFC Nifty Next 50 Index Fund - Direct Growth",
    "next 50":                  "HDFC Nifty Next 50 Index Fund - Direct Growth",

    # Pharma and Healthcare
    "hdfc pharma":              "HDFC Pharma and Healthcare Fund - Direct Growth",
    "pharma and healthcare":    "HDFC Pharma and Healthcare Fund - Direct Growth",
    "pharma fund":              "HDFC Pharma and Healthcare Fund - Direct Growth",
    "healthcare fund":          "HDFC Pharma and Healthcare Fund - Direct Growth",

    # Balanced Advantage
    "hdfc balanced advantage":  "HDFC Balanced Advantage Fund - Direct Growth",
    "balanced advantage":       "HDFC Balanced Advantage Fund - Direct Growth",
    "dynamic asset allocation": "HDFC Balanced Advantage Fund - Direct Growth",

    # Defence
    "hdfc defence":             "HDFC Defence Fund - Direct Growth",
    "defence fund":             "HDFC Defence Fund - Direct Growth",
    "defense fund":             "HDFC Defence Fund - Direct Growth",
}

# Sorted by length descending so longer (more specific) aliases match first.
_SORTED_ALIASES: list[tuple[str, str]] = sorted(
    _SCHEME_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True
)


# ── Public API ─────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    vectorstore_path: str = DEFAULT_VECTORSTORE_PATH,
) -> list[Document]:
    """Embed a query and retrieve the most relevant chunks from ChromaDB.

    Pipeline:
      1. Normalise query (Task 2.2).
      2. Detect canonical scheme name → build metadata filter (Task 2.3).
      3. Embed query with BGE query prefix (Task 2.1).
      4. Query ChromaDB (cosine similarity, top-k, optional where-filter).
      5. Apply score threshold (>=0.65) and return passing chunks.

    Args:
        query:             User's natural-language question (raw).
        top_k:             Maximum number of chunks to return (default 5).
        score_threshold:   Minimum cosine similarity score (default 0.65).
        vectorstore_path:  Path to ChromaDB persistent store.

    Returns:
        List of Documents ordered by descending similarity score.
        Each Document's metadata includes: source_url, scheme_name, document_type,
        fetch_date, chunk_index, chunk_text, and similarity_score.
        Returns an empty list when no chunks meet the threshold.
    """
    if not query or not query.strip():
        logger.warning("retrieve() called with empty query — returning empty list.")
        return []

    # Step 1: Query pre-processing (Task 2.2)
    normalised_query, detected_scheme = preprocess_query(query)
    logger.debug("Query normalised: %r → %r", query, normalised_query)
    if detected_scheme:
        logger.debug("Scheme detected in query: %r", detected_scheme)

    # Step 2: Build metadata pre-filter (Task 2.3)
    where_filter: dict[str, Any] | None = None
    if detected_scheme:
        where_filter = {"scheme_name": detected_scheme}
        logger.debug("Applying ChromaDB where-filter: %s", where_filter)

    # Step 3: Embed query with BGE query prefix (Task 2.1)
    model: SentenceTransformer = _get_or_load_model(DEFAULT_EMBEDDING_MODEL)
    prefixed_query = f"{_BGE_QUERY_PREFIX}{normalised_query}"
    query_embedding = model.encode(
        prefixed_query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()

    # Step 4: Search ChromaDB
    try:
        client = chromadb.PersistentClient(path=vectorstore_path)
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as exc:
        logger.error(
            "Could not open ChromaDB collection '%s' at '%s': %s",
            COLLECTION_NAME, vectorstore_path, exc,
        )
        logger.error("Run 'python scripts/ingest.py' to populate the vector store.")
        return []

    # Request more than top_k if filtering, so threshold cuts don't leave us short.
    n_results = min(top_k * 3 if where_filter else top_k * 2, collection.count() or 1)

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        query_kwargs["where"] = where_filter

    try:
        results = collection.query(**query_kwargs)
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    # Step 5: Apply score threshold and build Document list
    chunks: list[Document] = []
    documents_list = results.get("documents", [[]])[0]
    metadatas_list = results.get("metadatas", [[]])[0]
    distances_list = results.get("distances", [[]])[0]

    for doc_text, metadata, distance in zip(documents_list, metadatas_list, distances_list):
        # ChromaDB cosine distance: 0.0 = identical, 2.0 = opposite.
        # Convert to similarity score: similarity = 1 - (distance / 2)
        # (for normalised vectors, cosine distance ranges 0-2)
        similarity = 1.0 - (distance / 2.0)

        if similarity < score_threshold:
            logger.debug(
                "Chunk filtered (score %.3f < threshold %.3f): %s…",
                similarity, score_threshold, str(doc_text)[:60],
            )
            continue

        enriched_metadata = dict(metadata)
        enriched_metadata["similarity_score"] = round(similarity, 4)

        chunks.append(Document(text=doc_text or "", metadata=enriched_metadata))

        if len(chunks) >= top_k:
            break

    logger.info(
        "Retrieved %d chunk(s) for query %r (scheme filter: %s)",
        len(chunks), query[:60], detected_scheme or "none",
    )
    return chunks


# ── Task 2.2: Query Pre-processing ────────────────────────────────────────────

def preprocess_query(query: str) -> tuple[str, str | None]:
    """Normalise a raw query and detect any canonical scheme name within it.

    Steps:
      1. Strip leading/trailing whitespace.
      2. Lowercase.
      3. Collapse multiple whitespace characters to single spaces.
      4. Scan for scheme aliases (longest match first).

    Args:
        query: Raw user query string.

    Returns:
        Tuple of (normalised_query, canonical_scheme_name_or_None).
        The returned query is suitable for BGE embedding.
        The canonical scheme name (if found) is used for ChromaDB pre-filtering.
    """
    normalised = " ".join(query.strip().lower().split())

    detected_scheme: str | None = None
    for alias, canonical in _SORTED_ALIASES:
        if alias in normalised:
            detected_scheme = canonical
            logger.debug("Alias %r matched canonical scheme %r", alias, canonical)
            break

    return normalised, detected_scheme


def detect_scheme(query: str) -> str | None:
    """Return the canonical scheme name detected in a query, or None.

    Convenience wrapper around preprocess_query() for use in other modules
    (e.g. guardrails, API routes) that need scheme detection without full
    query normalisation.

    Args:
        query: Raw user query.

    Returns:
        Canonical scheme name string, or None if no scheme is detected.
    """
    _, scheme = preprocess_query(query)
    return scheme

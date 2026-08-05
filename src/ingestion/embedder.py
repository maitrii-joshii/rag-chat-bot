"""
Ingestion — Embedder (Tasks 1.5 & 1.6)

Task 1.5 — Metadata Enrichment:
  Expose ``enrich_metadata()`` as a standalone, testable function that
  validates and finalises the metadata dict that must be present on every
  chunk before upsert. (Metadata fields are first attached in chunker.py;
  this function is the canonical validation gate before storage.)

Task 1.6 — Embedder:
  1. Load ``BAAI/bge-small-en-v1.5`` via sentence-transformers (local, no API key).
  2. Prefix chunk texts with the BGE-recommended passage prefix for indexing.
  3. Batch-encode chunks and L2-normalise vectors for cosine similarity.
  4. Upsert (not add) embeddings + metadata into ChromaDB collection ``mf_faq_v1``.
  5. Idempotent: upserting the same chunk ID twice overwrites, never duplicates.

ChromaDB record schema (§3.4):
  {
    "id": "chunk_<url_slug>_<chunk_index>",
    "embedding": [...],        # 384-dim float list (bge-small)
    "metadata": {
      "source_url": str,
      "document_type": str,
      "scheme_name": str,
      "fetch_date": str,       # "YYYY-MM-DD"
      "chunk_index": int,
      "chunk_text": str
    }
  }
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

from src.ingestion.loader import Document

logger = logging.getLogger(__name__)

# ── Model & Collection Config ─────────────────────────────────────────────────
DEFAULT_EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
)
COLLECTION_NAME: str = os.getenv(
    "VECTORSTORE_COLLECTION", "mf_faq_v1"
)

# BGE-recommended prefix for *passage* (document) embeddings during indexing.
# Queries use a different prefix: "Represent this sentence for searching relevant passages: "
# (applied in retriever.py, not here).
_BGE_PASSAGE_PREFIX: str = "Represent this passage for retrieval: "

# Batch size for sentence-transformers encode() — keeps RAM usage bounded.
_EMBED_BATCH_SIZE: int = 32

# Required metadata fields — every chunk must have all of these before upsert.
_REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "source_url",
    "scheme_name",
    "document_type",
    "fetch_date",
    "chunk_index",
    "chunk_text",
)

# Module-level model cache — loaded once per process to avoid redundant downloads.
_model_cache: dict[str, SentenceTransformer] = {}


# ── Task 1.5: Metadata Enrichment ────────────────────────────────────────────

def enrich_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Validate and return an enriched metadata dict ready for ChromaDB upsert.

    Verifies all required fields are present and casts ``chunk_index`` to int
    so ChromaDB stores it as a number (enabling numeric filter queries later).

    Args:
        metadata: Metadata dict as produced by ``chunker.chunk()``.

    Returns:
        Validated metadata dict — same object, modified in-place and returned.

    Raises:
        ValueError: If any required field is missing or empty.
    """
    missing = [f for f in _REQUIRED_METADATA_FIELDS if not metadata.get(f) and metadata.get(f) != 0]
    if missing:
        raise ValueError(
            f"Chunk metadata is missing required fields: {missing}. "
            f"Got keys: {list(metadata.keys())}"
        )

    # Ensure chunk_index is int (ChromaDB metadata must be str/int/float/bool)
    metadata["chunk_index"] = int(metadata["chunk_index"])

    # Ensure chunk_text is a plain string (not None, not empty)
    if not isinstance(metadata["chunk_text"], str) or not metadata["chunk_text"].strip():
        raise ValueError("chunk_text metadata field must be a non-empty string.")

    return metadata


# ── Task 1.6: Embedder ────────────────────────────────────────────────────────

def embed_and_store(
    chunks: list[Document],
    vectorstore_path: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    collection_name: str = COLLECTION_NAME,
) -> int:
    """Generate BGE embeddings and upsert chunks into ChromaDB.

    Idempotent: each chunk is identified by a deterministic ID derived from
    its ``source_url`` and ``chunk_index``. Upserting the same ID twice
    overwrites the existing record — no duplicates are created.

    Args:
        chunks:           List of chunk Documents from ``chunker.chunk()``.
        vectorstore_path: Filesystem path to the ChromaDB persistent store.
        model_name:       HuggingFace model ID (defaults to bge-small-en-v1.5).
        collection_name:  ChromaDB collection name (defaults to mf_faq_v1).

    Returns:
        Number of chunks upserted into ChromaDB.

    Raises:
        ValueError: If any chunk fails metadata validation.
        RuntimeError: If the ChromaDB upsert fails.
    """
    if not chunks:
        logger.warning("embed_and_store called with 0 chunks — nothing to do.")
        return 0

    # ── Step 1: Validate metadata for all chunks ──────────────────────────────
    for chunk in chunks:
        enrich_metadata(chunk.metadata)  # raises ValueError on bad metadata

    # ── Step 2: Load model (cached) ───────────────────────────────────────────
    model = _get_or_load_model(model_name)

    # ── Step 3: Prepare texts with BGE passage prefix ─────────────────────────
    texts = [
        f"{_BGE_PASSAGE_PREFIX}{chunk.text}"
        for chunk in chunks
    ]

    # ── Step 4: Batch-encode and L2-normalise ────────────────────────────────
    logger.info(
        "Embedding %d chunks with %s (batch_size=%d)...",
        len(texts), model_name, _EMBED_BATCH_SIZE,
    )
    raw_embeddings: np.ndarray = model.encode(
        texts,
        batch_size=_EMBED_BATCH_SIZE,
        show_progress_bar=len(texts) > _EMBED_BATCH_SIZE,
        normalize_embeddings=True,   # L2-normalise for cosine similarity
        convert_to_numpy=True,
    )

    # ── Step 5: Open ChromaDB collection ─────────────────────────────────────
    client = chromadb.PersistentClient(path=vectorstore_path)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},  # cosine distance metric
    )

    # ── Step 6: Build upsert payloads in batches ──────────────────────────────
    ids: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, Any]] = []
    documents: list[str] = []

    for chunk, embedding in zip(chunks, raw_embeddings):
        chunk_id = _make_chunk_id(
            source_url=chunk.metadata["source_url"],
            chunk_index=chunk.metadata["chunk_index"],
        )
        # ChromaDB metadata values must be str | int | float | bool
        safe_meta = _sanitise_metadata(chunk.metadata)

        ids.append(chunk_id)
        embeddings.append(embedding.tolist())
        metadatas.append(safe_meta)
        documents.append(chunk.text)  # stored as the document string in ChromaDB

    # ── Step 7: Upsert (idempotent) in batches ────────────────────────────────
    _CHROMA_BATCH_SIZE = 100  # ChromaDB recommended max per upsert call
    total_upserted = 0

    for start in range(0, len(ids), _CHROMA_BATCH_SIZE):
        end = start + _CHROMA_BATCH_SIZE
        try:
            collection.upsert(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                metadatas=metadatas[start:end],
                documents=documents[start:end],
            )
            batch_count = len(ids[start:end])
            total_upserted += batch_count
            logger.debug(
                "Upserted batch [%d:%d] (%d records) into '%s'",
                start, end, batch_count, collection_name,
            )
        except Exception as exc:
            raise RuntimeError(
                f"ChromaDB upsert failed for batch [{start}:{end}]: {exc}"
            ) from exc

    logger.info(
        "Successfully upserted %d chunks into ChromaDB collection '%s' at '%s'",
        total_upserted, collection_name, vectorstore_path,
    )
    return total_upserted


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_load_model(model_name: str) -> SentenceTransformer:
    """Load the SentenceTransformer model, using the module-level cache."""
    if model_name not in _model_cache:
        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = SentenceTransformer(model_name)
        logger.info("Model loaded — embedding dim: %d", _model_cache[model_name].get_embedding_dimension())
    return _model_cache[model_name]


def _make_chunk_id(source_url: str, chunk_index: int) -> str:
    """Derive a deterministic, stable chunk ID for ChromaDB.

    Format: ``chunk_<8-char-url-hash>_<chunk_index>``

    The URL is hashed (not included raw) to keep IDs short and safe for
    ChromaDB's ID constraints, while remaining deterministic across runs.
    """
    url_hash = hashlib.sha256(source_url.encode()).hexdigest()[:8]
    # Sanitise URL for a human-readable slug (optional prefix for readability)
    slug = re.sub(r"[^a-z0-9]+", "_", source_url.lower().split("//")[-1])[:40]
    return f"chunk_{slug}_{url_hash}_{chunk_index}"


def _sanitise_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of metadata with all values cast to ChromaDB-safe types.

    ChromaDB only accepts: str, int, float, bool.
    Lists, dicts, and None values are converted to strings.
    """
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            safe[key] = value
        elif value is None:
            safe[key] = ""
        else:
            safe[key] = str(value)
    return safe


def get_collection_stats(
    vectorstore_path: str,
    collection_name: str = COLLECTION_NAME,
) -> dict[str, Any]:
    """Return basic stats about the ChromaDB collection.

    Used by the health check endpoint and post-ingestion verification.

    Returns:
        Dict with ``collection_name``, ``chunk_count``, ``vectorstore_path``.
        Returns ``chunk_count: 0`` if the collection does not yet exist.
    """
    try:
        client = chromadb.PersistentClient(path=vectorstore_path)
        collection = client.get_collection(name=collection_name)
        count = collection.count()
    except Exception:
        count = 0

    return {
        "collection_name": collection_name,
        "chunk_count": count,
        "vectorstore_path": vectorstore_path,
    }

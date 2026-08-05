"""
Ingestion — Text Chunker (Task 1.4)

Responsibilities:
  1. Split clean text at section boundaries (headings, paragraph breaks).
  2. Target chunk size: ~500 tokens with ~100-token overlap.
  3. Preserve [TABLE]...[/TABLE] blocks as single, unbroken chunks.
  4. Enrich each chunk with parent document metadata:
       source_url, scheme_name, document_type, fetch_date, chunk_index, chunk_text.

Uses LangChain's RecursiveCharacterTextSplitter with a character-count proxy
for tokens (1 token ≈ 4 characters for English financial text).
"""

from __future__ import annotations

import logging
import re
from copy import deepcopy

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingestion.loader import Document

logger = logging.getLogger(__name__)

# ── Chunk Configuration (Task 1.4) ────────────────────────────────────────────
# 1 token ≈ 4 chars for English text — a widely-used proxy that avoids the
# overhead of loading a full tokenizer during offline ingestion.
_CHARS_PER_TOKEN: int = 4

CHUNK_SIZE_TOKENS: int = 500
CHUNK_OVERLAP_TOKENS: int = 100

_CHUNK_SIZE_CHARS: int = CHUNK_SIZE_TOKENS * _CHARS_PER_TOKEN     # 2000
_CHUNK_OVERLAP_CHARS: int = CHUNK_OVERLAP_TOKENS * _CHARS_PER_TOKEN  # 400

# ── Table Sentinel ────────────────────────────────────────────────────────────
_TABLE_START = "[TABLE]"
_TABLE_END = "[/TABLE]"
_TABLE_BLOCK_RE = re.compile(
    r"\[TABLE\].*?\[/TABLE\]",
    re.DOTALL,
)

# ── LangChain Splitter ────────────────────────────────────────────────────────
# Split preferentially at: double newlines → single newlines → spaces → chars.
# This preserves paragraph/section boundaries as long as possible.
_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=_CHUNK_SIZE_CHARS,
    chunk_overlap=_CHUNK_OVERLAP_CHARS,
    separators=["\n\n", "\n", " ", ""],
    length_function=len,
    is_separator_regex=False,
)


def chunk(document: Document) -> list[Document]:
    """Split a pre-processed Document into retrieval-friendly chunks.

    Algorithm:
      1. Extract all [TABLE]...[/TABLE] blocks as protected segments.
      2. Replace each table block in the text with a unique placeholder token.
      3. Run RecursiveCharacterTextSplitter on the remaining text.
      4. Re-inject table blocks wherever their placeholder appears
         (each table becomes its own chunk if it would span multiple chunks,
         otherwise it merges into the surrounding split).
      5. Attach metadata to every chunk (source_url, scheme_name, document_type,
         fetch_date, chunk_index, chunk_text).

    Args:
        document: Pre-processed Document from the loader.

    Returns:
        List of Documents — one per chunk — inheriting parent metadata plus
        ``chunk_index`` (0-based) and ``chunk_text`` (the chunk string itself).
        Returns an empty list if the document has no usable text.
    """
    text = document.text.strip()
    if not text:
        logger.warning("chunk() received empty document for '%s'", document.metadata.get("scheme_name"))
        return []

    # ── Step 1: Extract table blocks ──────────────────────────────────────────
    tables: list[str] = _TABLE_BLOCK_RE.findall(text)
    table_placeholders: dict[str, str] = {}

    protected_text = text
    for idx, table in enumerate(tables):
        placeholder = f"__TABLE_{idx}__"
        table_placeholders[placeholder] = table
        protected_text = protected_text.replace(table, placeholder, 1)

    # ── Step 2: Split the non-table text ─────────────────────────────────────
    raw_chunks: list[str] = _SPLITTER.split_text(protected_text)

    # ── Step 3: Expand placeholders back into table content ──────────────────
    expanded_chunks: list[str] = []
    for raw_chunk in raw_chunks:
        expanded = raw_chunk
        for placeholder, table_text in table_placeholders.items():
            if placeholder in expanded:
                expanded = expanded.replace(placeholder, table_text)
        expanded = expanded.strip()
        if expanded:
            expanded_chunks.append(expanded)

    # Handle any table blocks that landed entirely in their own chunk (placeholder only)
    # — already handled above. But tables not referenced in any split chunk
    # (e.g. at the very end of a document) need to be appended.
    referenced_placeholders = set()
    for ch in expanded_chunks:
        for placeholder in table_placeholders:
            if placeholder in ch or table_placeholders[placeholder] in ch:
                referenced_placeholders.add(placeholder)

    for placeholder, table_text in table_placeholders.items():
        if placeholder not in referenced_placeholders:
            expanded_chunks.append(table_text)

    if not expanded_chunks:
        logger.warning("Chunker produced 0 chunks for '%s'", document.metadata.get("scheme_name"))
        return []

    # ── Step 4: Build Document objects with enriched metadata ─────────────────
    chunks: list[Document] = []
    for i, chunk_text in enumerate(expanded_chunks):
        if not chunk_text.strip():
            continue

        chunk_metadata = deepcopy(document.metadata)
        chunk_metadata["chunk_index"] = i
        chunk_metadata["chunk_text"] = chunk_text  # stored in vector store metadata

        chunks.append(Document(text=chunk_text, metadata=chunk_metadata))

    logger.info(
        "Chunked '%s' → %d chunks (avg %.0f chars)",
        document.metadata.get("scheme_name", "unknown"),
        len(chunks),
        sum(len(c.text) for c in chunks) / max(len(chunks), 1),
    )
    return chunks

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/ingest.py — Ingestion Pipeline CLI Entry Point (Tasks 1.7 & 1.8)

Task 1.7 — Ingestion Script:
  Orchestrates the full offline ingestion pipeline end-to-end:
    Corpus YAML → Loader → Preprocessor → Chunker → Embedder → ChromaDB

Task 1.8 — Corpus Config Loader:
  Parses data/corpus.yml, validates all sources against the domain whitelist,
  and yields typed CorpusSource objects ready for the pipeline.

Usage:
  # Full ingestion (all 12 schemes)
  python scripts/ingest.py --config data/corpus.yml --output data/vectorstore

  # Forced full re-index (wipes existing collection first)
  python scripts/ingest.py --config data/corpus.yml --output data/vectorstore --force

  # Dry run — validate corpus.yml without fetching or embedding
  python scripts/ingest.py --config data/corpus.yml --dry-run

  # Health check — report ChromaDB stats without re-running ingestion
  python scripts/ingest.py --output data/vectorstore --health-check

  # Single scheme (for quick testing)
  python scripts/ingest.py --config data/corpus.yml --output data/vectorstore --scheme "HDFC Small Cap Fund - Direct Growth"

Exit codes:
  0 — All sources processed successfully
  1 — One or more sources failed (partial failure)
  2 — Fatal error (corpus parse error, bad path, etc.)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Force UTF-8 on Windows (cp1252 codec cannot handle box-drawing / em-dashes).
# Must happen BEFORE logging.basicConfig captures sys.stdout.
import io as _io
if isinstance(sys.stdout, _io.TextIOWrapper):
    sys.stdout = _io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )
if isinstance(sys.stderr, _io.TextIOWrapper):
    sys.stderr = _io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )

# ── Logging Setup ─────────────────────────────────────────────────────────────
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
))
logging.root.addHandler(_handler)
logging.root.setLevel(logging.INFO)
logger = logging.getLogger("ingest")


# ── Corpus Source Model (Task 1.8) ────────────────────────────────────────────

@dataclass(frozen=True)
class CorpusSource:
    """A single validated source entry from corpus.yml."""
    url: str
    scheme_name: str
    document_type: str


# ── Argument Parser ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ingest.py",
        description=(
            "RAG Mutual Fund FAQ Assistant — Corpus Ingestion Pipeline\n"
            "Fetches Groww scheme pages, chunks text, embeds with BGE, "
            "and stores in ChromaDB."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data/corpus.yml"),
        metavar="PATH",
        help="Path to corpus registry YAML (default: data/corpus.yml).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/vectorstore"),
        metavar="PATH",
        help="ChromaDB persistent store directory (default: data/vectorstore).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate the ChromaDB collection before ingestion (full re-index).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate corpus.yml and print sources without fetching or embedding.",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Print ChromaDB collection stats and exit (no ingestion).",
    )
    parser.add_argument(
        "--scheme",
        type=str,
        default=None,
        metavar="NAME",
        help="Process only the named scheme (exact match, for testing).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args()


# ── Task 1.8: Corpus Config Loader ───────────────────────────────────────────

def load_corpus(config_path: Path) -> list[CorpusSource]:
    """Parse corpus.yml and return a validated list of CorpusSource objects.

    Validates:
      - File exists and is valid YAML
      - ``sources`` key is present and non-empty
      - Every source has ``url``, ``scheme``, and ``type`` fields
      - Every URL's domain is in the whitelist (uses loader's _validate_domain)

    Args:
        config_path: Path to the corpus YAML file.

    Returns:
        List of CorpusSource objects, one per source entry.

    Raises:
        SystemExit(2): On any parse or validation error.
    """
    from src.ingestion.loader import _validate_domain

    if not config_path.exists():
        logger.error("Corpus config not found: %s", config_path)
        sys.exit(2)

    logger.info("Loading corpus registry: %s", config_path)
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            corpus: dict[str, Any] = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        logger.error("Failed to parse corpus YAML: %s", exc)
        sys.exit(2)

    if not isinstance(corpus, dict):
        logger.error("corpus.yml must be a YAML mapping at the top level.")
        sys.exit(2)

    raw_sources = corpus.get("sources", [])
    if not raw_sources:
        logger.error("corpus.yml contains no 'sources' entries.")
        sys.exit(2)

    sources: list[CorpusSource] = []
    errors: list[str] = []

    for i, entry in enumerate(raw_sources):
        # Validate required fields
        url         = entry.get("url", "").strip()
        scheme_name = entry.get("scheme", "").strip()
        doc_type    = entry.get("type", "scheme_page").strip()

        if not url:
            errors.append(f"Source [{i}]: missing 'url' field.")
            continue
        if not scheme_name:
            errors.append(f"Source [{i}] ({url}): missing 'scheme' field.")
            continue

        # Validate domain whitelist
        try:
            _validate_domain(url)
        except ValueError as exc:
            errors.append(f"Source [{i}] ({scheme_name}): {exc}")
            continue

        sources.append(CorpusSource(url=url, scheme_name=scheme_name, document_type=doc_type))

    if errors:
        for err in errors:
            logger.error("Corpus validation error — %s", err)
        logger.error("%d validation error(s) found in %s. Aborting.", len(errors), config_path)
        sys.exit(2)

    amc = corpus.get("amc", "Unknown AMC")
    logger.info(
        "Corpus loaded: %s — %d source(s) across %d scheme(s)",
        amc, len(sources), len(corpus.get("schemes", sources)),
    )
    return sources


# ── Task 1.7: Ingestion Pipeline Orchestrator ─────────────────────────────────

def run_health_check(output_path: Path) -> None:
    """Print ChromaDB collection stats and exit."""
    from src.ingestion.embedder import get_collection_stats

    stats = get_collection_stats(str(output_path))
    print()
    print("-" * 50)
    print("  ChromaDB Health Check")
    print("-" * 50)
    print(f"  Collection : {stats['collection_name']}")
    print(f"  Chunk count: {stats['chunk_count']}")
    print(f"  Store path : {stats['vectorstore_path']}")
    print("-" * 50)
    if stats["chunk_count"] == 0:
        logger.warning("Vector store is empty — run ingestion to populate it.")
        sys.exit(1)
    sys.exit(0)


def _drop_collection_if_exists(output_path: Path, collection_name: str) -> None:
    """Delete the ChromaDB collection for a full re-index (--force flag)."""
    import chromadb
    from src.ingestion.embedder import COLLECTION_NAME

    name = collection_name or COLLECTION_NAME
    try:
        client = chromadb.PersistentClient(path=str(output_path))
        client.delete_collection(name=name)
        logger.info("Dropped existing collection '%s' (--force mode).", name)
    except Exception:
        logger.debug("Collection '%s' did not exist — nothing to drop.", name)


def run_pipeline(
    sources: list[CorpusSource],
    output_path: Path,
    dry_run: bool = False,
    force: bool = False,
    scheme_filter: str | None = None,
) -> int:
    """Execute the full ingestion pipeline for all corpus sources.

    Pipeline per source:
      load_url() → preprocess() → chunk() → embed_and_store()

    Args:
        sources:       Validated CorpusSource objects from load_corpus().
        output_path:   ChromaDB store directory.
        dry_run:       If True, skip fetching and embedding.
        force:         If True, drop the collection before starting.
        scheme_filter: If set, only process the scheme matching this name.

    Returns:
        Exit code (0 = all success, 1 = at least one failure).
    """
    from src.ingestion.loader import load_url
    from src.ingestion.preprocessor import preprocess
    from src.ingestion.chunker import chunk
    from src.ingestion.embedder import embed_and_store, COLLECTION_NAME

    # Apply scheme filter
    if scheme_filter:
        filtered = [s for s in sources if s.scheme_name == scheme_filter]
        if not filtered:
            logger.error(
                "No source found for scheme '%s'. Available: %s",
                scheme_filter,
                [s.scheme_name for s in sources],
            )
            return 2
        sources = filtered
        logger.info("Scheme filter applied — processing 1/%d source(s).", len(sources))

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print()
        print("-" * 60)
        print("  DRY RUN -- No HTTP requests or embeddings will be made")
        print("-" * 60)
        for i, source in enumerate(sources, 1):
            print(f"  [{i:02d}] {source.scheme_name}")
            print(f"        {source.url}")
        print(f"\n  Total: {len(sources)} source(s) validated.")
        return 0

    # Force full re-index if requested
    if force:
        _drop_collection_if_exists(output_path, COLLECTION_NAME)

    # -- Pipeline execution ----------------------------------------------------
    pipeline_start = time.perf_counter()
    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []  # (scheme_name, error_message)
    total_chunks = 0

    print()
    print("-" * 60)
    print("  RAG Mutual Fund FAQ Assistant -- Ingestion Pipeline")
    print("-" * 60)
    print(f"  Sources   : {len(sources)}")
    print(f"  Output    : {output_path}")
    print(f"  Force     : {force}")
    print("-" * 60)
    print()

    for i, source in enumerate(sources, 1):
        source_start = time.perf_counter()
        print(f"[{i:02d}/{len(sources):02d}] {source.scheme_name}")
        print(f"        URL : {source.url}")

        try:
            # Step 1 -- Fetch & parse HTML
            document = load_url(source.url, source.scheme_name)
            raw_chars = len(document.text)
            print(f"        Fetched  : {raw_chars:,} chars")

            # Step 2 -- Clean text
            document.text = preprocess(document.text)
            clean_chars = len(document.text)
            print(f"        Cleaned  : {clean_chars:,} chars")

            if clean_chars < 50:
                raise ValueError(
                    f"Preprocessed text too short ({clean_chars} chars) -- "
                    "likely a rendering/JS issue on the source page."
                )

            # Step 3 -- Chunk
            chunks = chunk(document)
            if not chunks:
                raise ValueError("Chunker produced 0 chunks -- check preprocessed content.")
            print(f"        Chunks   : {len(chunks)} (~{clean_chars // max(len(chunks), 1):,} chars avg)")

            # Step 4 -- Embed & store
            upserted = embed_and_store(chunks, str(output_path))
            total_chunks += upserted
            elapsed = time.perf_counter() - source_start
            print(f"        Upserted : {upserted}  OK  ({elapsed:.1f}s)")

            succeeded.append(source.scheme_name)

        except Exception as exc:
            elapsed = time.perf_counter() - source_start
            error_msg = str(exc)
            logger.error(
                "[%02d/%02d] FAILED -- %s: %s (%.1fs)",
                i, len(sources), source.scheme_name, error_msg, elapsed,
            )
            failed.append((source.scheme_name, error_msg))

        print()

    # -- Summary ---------------------------------------------------------------
    total_elapsed = time.perf_counter() - pipeline_start
    print("-" * 60)
    print("  INGESTION SUMMARY")
    print("-" * 60)
    print(f"  Sources processed : {len(sources)}")
    print(f"  Succeeded         : {len(succeeded)}")
    print(f"  Failed            : {len(failed)}")
    print(f"  Total chunks      : {total_chunks:,}")
    print(f"  Total time        : {total_elapsed:.1f}s")

    if failed:
        print()
        print("  FAILURES:")
        for scheme_name, error_msg in failed:
            print(f"    [FAIL] {scheme_name}")
            print(f"           {error_msg}")

    print("-" * 60)

    return 1 if failed else 0


# -- Entry Point ---------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure the project root is on sys.path when running from any directory
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Health check mode — no ingestion needed
    if args.health_check:
        run_health_check(args.output)
        return  # run_health_check exits via sys.exit()

    # Load and validate corpus
    sources = load_corpus(args.config)

    # Run pipeline
    exit_code = run_pipeline(
        sources=sources,
        output_path=args.output,
        dry_run=args.dry_run,
        force=args.force,
        scheme_filter=args.scheme,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

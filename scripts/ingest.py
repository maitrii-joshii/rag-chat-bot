#!/usr/bin/env python3
"""
scripts/ingest.py — Ingestion Pipeline CLI Entry Point (Phase 1 implementation)

Orchestrates the full offline ingestion pipeline:
  1. Load corpus registry from data/corpus.yml
  2. For each scheme URL → fetch HTML (loader) → clean text (preprocessor)
  3. Chunk into ~500-token segments (chunker)
  4. Generate BGE embeddings and upsert into ChromaDB (embedder)

Usage:
  python scripts/ingest.py --config data/corpus.yml --output data/vectorstore

Phase 0: Script scaffold with argument parsing and pipeline skeleton.
Phase 1: Full implementation of each pipeline step.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest HDFC Mutual Fund scheme pages into ChromaDB."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data/corpus.yml"),
        help="Path to the corpus registry YAML file (default: data/corpus.yml).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/vectorstore"),
        help="Path to the ChromaDB persistent store directory (default: data/vectorstore).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse corpus.yml and validate URLs without fetching or embedding.",
    )
    return parser.parse_args()


def load_corpus(config_path: Path) -> dict:
    """Parse the corpus.yml file and return the registry dict."""
    import yaml  # pyyaml

    if not config_path.exists():
        print(f"[ERROR] Corpus config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with config_path.open("r", encoding="utf-8") as fh:
        corpus = yaml.safe_load(fh)

    sources = corpus.get("sources", [])
    print(f"[INFO] Loaded {len(sources)} source(s) from {config_path}")
    return corpus


def run_pipeline(corpus: dict, output_path: Path, dry_run: bool = False) -> None:
    """Execute the full ingestion pipeline for all corpus sources.

    Phase 0: Skeleton only — individual steps raise NotImplementedError.
    Phase 1: Replace each NotImplementedError block with real implementation.
    """
    from src.ingestion.loader import load_url
    from src.ingestion.preprocessor import preprocess
    from src.ingestion.chunker import chunk
    from src.ingestion.embedder import embed_and_store

    sources = corpus.get("sources", [])
    total_chunks = 0

    for source in sources:
        url         = source["url"]
        scheme_name = source["scheme"]

        print(f"[INFO] Processing: {scheme_name}")
        print(f"       URL: {url}")

        if dry_run:
            print(f"       [DRY RUN] Skipping fetch.")
            continue

        try:
            # Step 1 — Fetch & parse HTML
            document = load_url(url, scheme_name)

            # Step 2 — Clean text
            document.text = preprocess(document.text)

            # Step 3 — Chunk
            chunks = chunk(document)
            print(f"       Chunks generated: {len(chunks)}")

            # Step 4 — Embed & store
            upserted = embed_and_store(chunks, str(output_path))
            total_chunks += upserted
            print(f"       Chunks upserted: {upserted}")

        except NotImplementedError as exc:
            print(f"[WARN] Phase 0 stub encountered: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"[ERROR] Failed to process {url}: {exc}", file=sys.stderr)

    print(f"\n[DONE] Total chunks upserted: {total_chunks}")


def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("  RAG Mutual Fund FAQ Assistant — Ingestion Pipeline")
    print("=" * 60)

    corpus = load_corpus(args.config)
    run_pipeline(corpus, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/evaluate.py — Batch Evaluation Script (Phase 5 implementation)

Runs a predefined gold-standard Q&A set through the full RAG pipeline and
reports retrieval + generation accuracy metrics.

Metrics computed:
  - Hit rate: % of queries where the correct chunk is in top-k results
  - Answer coverage: % of answers that contain expected key terms
  - Refusal rate: % of advisory/OOS queries correctly refused

Usage:
  python scripts/evaluate.py --vectorstore data/vectorstore

Phase 0: Script scaffold with argument parsing and gold-standard test stubs.
Phase 5: Full implementation with metric computation and HTML report.
"""

from __future__ import annotations

import argparse
from pathlib import Path


# ── Gold-standard Test Set ────────────────────────────────────────────────────
# Each entry: { query, expected_scheme, expected_key_terms, should_refuse }
GOLD_STANDARD: list[dict] = [
    # Factual queries (should answer)
    {
        "query": "What is the expense ratio of HDFC Small Cap Fund?",
        "expected_scheme": "HDFC Small Cap Fund - Direct Growth",
        "expected_key_terms": ["expense ratio", "%"],
        "should_refuse": False,
    },
    {
        "query": "What is the exit load for HDFC Large Cap Fund?",
        "expected_scheme": "HDFC Large Cap Fund - Direct Growth",
        "expected_key_terms": ["exit load"],
        "should_refuse": False,
    },
    {
        "query": "What is the minimum SIP amount for HDFC Mid Cap Fund?",
        "expected_scheme": "HDFC Mid Cap Fund - Direct Growth",
        "expected_key_terms": ["SIP", "minimum", "₹"],
        "should_refuse": False,
    },
    # Advisory / out-of-scope queries (should refuse)
    {
        "query": "Should I invest in HDFC Small Cap Fund?",
        "expected_scheme": None,
        "expected_key_terms": [],
        "should_refuse": True,
    },
    {
        "query": "Which is better — HDFC Small Cap or Mid Cap?",
        "expected_scheme": None,
        "expected_key_terms": [],
        "should_refuse": True,
    },
    {
        "query": "What is the weather today?",
        "expected_scheme": None,
        "expected_key_terms": [],
        "should_refuse": True,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the RAG pipeline against a gold-standard Q&A set."
    )
    parser.add_argument(
        "--vectorstore",
        type=Path,
        default=Path("data/vectorstore"),
        help="Path to the ChromaDB persistent store (default: data/vectorstore).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write evaluation results as JSON.",
    )
    return parser.parse_args()


def evaluate(vectorstore_path: Path) -> dict:
    """Run all gold-standard queries and compute metrics.

    Phase 0: Stub — returns empty metrics dict.
    Phase 5: Full implementation.
    """
    raise NotImplementedError(
        "evaluate.evaluate is a Phase 0 stub. Full implementation in Phase 5."
    )


def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("  RAG Mutual Fund FAQ Assistant — Evaluation")
    print("=" * 60)
    print(f"[INFO] Gold-standard queries: {len(GOLD_STANDARD)}")
    print("[WARN] Evaluation is a Phase 0 stub — implement in Phase 5.")


if __name__ == "__main__":
    main()

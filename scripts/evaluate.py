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
    """Run all gold-standard queries and compute metrics."""
    # We set VECTORSTORE_PATH in the environment so src.main picks it up
    import os
    os.environ["VECTORSTORE_PATH"] = str(vectorstore_path)
    
    # Import app inside the function so env vars are applied
    from fastapi.testclient import TestClient
    from src.main import app
    
    client = TestClient(app)
    
    total = len(GOLD_STANDARD)
    hits = 0
    coverage = 0
    correct_refusals = 0
    factual_count = sum(1 for q in GOLD_STANDARD if not q["should_refuse"])
    refusal_count = total - factual_count
    
    for item in GOLD_STANDARD:
        query = item["query"]
        print(f"Testing: {query}")
        
        response = client.post("/api/chat", json={"query": query, "session_id": "eval"})
        if response.status_code != 200:
            print(f"  [ERROR] Status {response.status_code}: {response.text}")
            continue
            
        data = response.json()
        
        if item["should_refuse"]:
            if data["query_type"] not in ["factual"]:
                correct_refusals += 1
                print("  [OK] Correctly refused.")
            else:
                print(f"  [FAIL] Expected refusal, but got factual answer.")
            continue
            
        # It's a factual query
        answer = data["answer"]
        citation = data["citation"]
        
        # 1. Hit Rate Check
        if citation and citation["scheme_name"] == item["expected_scheme"]:
            hits += 1
            print("  [OK] Hit: correct scheme retrieved.")
        else:
            got = citation["scheme_name"] if citation else "None"
            print(f"  [FAIL] Miss: expected {item['expected_scheme']}, got {got}")
            
        # 2. Answer Coverage Check
        all_terms_present = True
        for term in item["expected_key_terms"]:
            if term.lower() not in answer.lower():
                all_terms_present = False
                print(f"  [FAIL] Missing expected term in answer: '{term}'")
        
        if all_terms_present:
            coverage += 1
            if item["expected_key_terms"]:
                 print("  [OK] Coverage: all key terms present in answer.")
                 
    hit_rate = (hits / factual_count) * 100 if factual_count else 0
    coverage_rate = (coverage / factual_count) * 100 if factual_count else 0
    refusal_rate = (correct_refusals / refusal_count) * 100 if refusal_count else 0
    
    return {
        "hit_rate": hit_rate,
        "coverage_rate": coverage_rate,
        "refusal_rate": refusal_rate,
        "total": total,
    }

def main() -> None:
    args = parse_args()

    print("=" * 60)
    print("  RAG Mutual Fund FAQ Assistant — Evaluation")
    print("=" * 60)
    print(f"[INFO] Gold-standard queries: {len(GOLD_STANDARD)}")
    
    metrics = evaluate(args.vectorstore)
    
    print("=" * 60)
    print("  Evaluation Results")
    print("=" * 60)
    print(f"Hit Rate (Correct Retrieval): {metrics['hit_rate']:.1f}%")
    print(f"Answer Coverage (Key Terms):  {metrics['coverage_rate']:.1f}%")
    print(f"Refusal Rate (Guardrails):    {metrics['refusal_rate']:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    main()

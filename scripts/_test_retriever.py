"""Smoke tests for retriever (Tasks 2.1-2.3) and reranker."""
import sys
sys.path.insert(0, ".")

from src.retrieval.retriever import preprocess_query, detect_scheme, retrieve
from src.retrieval.reranker import rerank
from src.ingestion.loader import Document

# ── Test 2.2: preprocess_query ────────────────────────────────────────────────
print("Testing preprocess_query (Task 2.2)...")

# Lowercase normalisation
q, scheme = preprocess_query("  What is the EXPENSE RATIO?  ")
assert q == "what is the expense ratio?", f"Bad normalisation: {q!r}"
assert scheme is None, f"Expected None, got {scheme!r}"
print("  PASS: lowercase normalisation")

# Scheme detection — specific alias
q, scheme = preprocess_query("What is the expense ratio of HDFC Small Cap fund?")
assert scheme == "HDFC Small Cap Fund - Direct Growth", f"Wrong scheme: {scheme!r}"
print(f"  PASS: 'small cap' detected -> {scheme}")

q, scheme = preprocess_query("Tell me about HDFC Gold ETF")
assert scheme == "HDFC Gold ETF Fund of Fund - Direct Plan Growth", f"Wrong scheme: {scheme!r}"
print(f"  PASS: 'Gold ETF' detected -> {scheme}")

q, scheme = preprocess_query("minimum SIP for HDFC mid cap fund?")
assert scheme == "HDFC Mid Cap Fund - Direct Growth", f"Wrong scheme: {scheme!r}"
print(f"  PASS: 'mid cap' detected -> {scheme}")

q, scheme = preprocess_query("What is HDFC Defence Fund about?")
assert scheme == "HDFC Defence Fund - Direct Growth", f"Wrong scheme: {scheme!r}"
print(f"  PASS: 'Defence Fund' detected -> {scheme}")

q, scheme = preprocess_query("What is the weather today?")
assert scheme is None, f"Expected None for unrelated query, got {scheme!r}"
print("  PASS: unrelated query returns None scheme")

# ── Test detect_scheme convenience wrapper ────────────────────────────────────
print("\nTesting detect_scheme wrapper...")
assert detect_scheme("HDFC Balanced Advantage fund details") == "HDFC Balanced Advantage Fund - Direct Growth"
assert detect_scheme("random question") is None
print("  PASS: detect_scheme works correctly")

# ── Test 2.3: Metadata filter construction ────────────────────────────────────
# (We verify the filter logic by checking preprocess_query output)
print("\nTesting metadata pre-filter logic (Task 2.3)...")
_, scheme = preprocess_query("What is the exit load for HDFC Pharma and Healthcare fund?")
assert scheme == "HDFC Pharma and Healthcare Fund - Direct Growth"
print(f"  PASS: filter would be applied for: {scheme}")

_, scheme = preprocess_query("What is the NAV of Nifty Next 50?")
assert scheme == "HDFC Nifty Next 50 Index Fund - Direct Growth"
print(f"  PASS: filter would be applied for: {scheme}")

# ── Test reranker pass-through ─────────────────────────────────────────────────
print("\nTesting reranker pass-through (MVP mode)...")
chunks = [
    Document(text="Expense ratio is 0.68%", metadata={"similarity_score": 0.92}),
    Document(text="Exit load is 1%", metadata={"similarity_score": 0.85}),
]
reranked = rerank("What is the expense ratio?", chunks)
assert len(reranked) == 2
assert reranked[0].text == chunks[0].text, "Pass-through should preserve order"
print("  PASS: reranker pass-through preserves order and count")

# Empty input
assert rerank("query", []) == []
print("  PASS: reranker handles empty chunks")

# ── Test retrieve with empty/invalid vectorstore ───────────────────────────────
print("\nTesting retrieve with missing vectorstore (graceful fallback)...")
result = retrieve("What is the expense ratio?", vectorstore_path="./data/does_not_exist")
assert result == [], f"Expected [] on missing store, got {result}"
print("  PASS: retrieve returns [] when vectorstore missing")

print()
print("All smoke tests passed.")

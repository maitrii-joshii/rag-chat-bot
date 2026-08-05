import gc
import os
import shutil
import sys
import tempfile

sys.path.insert(0, ".")

from src.ingestion.loader import Document
from src.ingestion.embedder import (
    COLLECTION_NAME,
    _make_chunk_id,
    _sanitise_metadata,
    embed_and_store,
    enrich_metadata,
    get_collection_stats,
)

print("PASS imports")

# ── Test 1.5: enrich_metadata validation ─────────────────────────────────────
good_meta = {
    "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "scheme_name": "HDFC Small Cap Fund - Direct Growth",
    "document_type": "scheme_page",
    "fetch_date": "2026-08-05",
    "chunk_index": 0,
    "chunk_text": "The expense ratio of HDFC Small Cap Fund is 0.68%.",
}
result = enrich_metadata(good_meta.copy())
assert result["chunk_index"] == 0
print("PASS enrich_metadata: valid metadata accepted")

try:
    enrich_metadata({"source_url": "https://groww.in/test"})
    print("FAIL: should have raised ValueError")
except ValueError:
    print("PASS enrich_metadata: missing fields raise ValueError")

# ── Test chunk ID determinism ─────────────────────────────────────────────────
url = "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
cid = _make_chunk_id(url, 3)
assert cid.startswith("chunk_"), f"Bad prefix: {cid}"
assert cid.endswith("_3"), f"Bad suffix: {cid}"
assert cid == _make_chunk_id(url, 3), "IDs not deterministic"
print("PASS chunk ID: deterministic —", cid)

# ── Test metadata sanitisation ────────────────────────────────────────────────
raw = {"key": [1, 2, 3], "none_val": None, "num": 42, "text": "hello"}
safe = _sanitise_metadata(raw)
assert safe["key"] == "[1, 2, 3]"
assert safe["none_val"] == ""
assert safe["num"] == 42
assert safe["text"] == "hello"
print("PASS _sanitise_metadata: types normalised correctly")

# ── Test 1.6: embed_and_store end-to-end ─────────────────────────────────────
print()
print("Loading BGE model and running embed_and_store...")

chunks = [
    Document(
        text="The expense ratio of HDFC Small Cap Fund Direct Growth is 0.68% per annum.",
        metadata={
            "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "scheme_name": "HDFC Small Cap Fund - Direct Growth",
            "document_type": "scheme_page",
            "fetch_date": "2026-08-05",
            "chunk_index": 0,
            "chunk_text": "Expense ratio is 0.68%.",
        },
    ),
    Document(
        text="The exit load for HDFC Small Cap Fund is 1% if redeemed within 1 year.",
        metadata={
            "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "scheme_name": "HDFC Small Cap Fund - Direct Growth",
            "document_type": "scheme_page",
            "fetch_date": "2026-08-05",
            "chunk_index": 1,
            "chunk_text": "Exit load is 1% within 1 year.",
        },
    ),
]

# Use a named temp dir and clean it up manually to avoid Windows file-lock issues
# with ChromaDB's HNSW binary files being held open by the client.
tmpdir = tempfile.mkdtemp()
try:
    upserted = embed_and_store(chunks, tmpdir)
    assert upserted == 2, f"Expected 2, got {upserted}"
    print("PASS embed_and_store: upserted", upserted, "chunks")

    # Idempotency: upsert same chunks again — count must stay at 2
    embed_and_store(chunks, tmpdir)
    stats = get_collection_stats(tmpdir)
    assert stats["chunk_count"] == 2, f"Expected count=2 after re-upsert, got {stats['chunk_count']}"
    print("PASS idempotency: count =", stats["chunk_count"], "(no duplicates)")
    print("PASS get_collection_stats:", stats)

finally:
    # Force garbage collection to release ChromaDB's internal file handles
    # before attempting directory removal (Windows-specific requirement).
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)

print()
print("All smoke tests passed.")

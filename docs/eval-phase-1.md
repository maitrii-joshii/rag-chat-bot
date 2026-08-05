# Evaluation Criteria — Phase 1: Data Ingestion Pipeline

> **Phase**: 1 — Data Pipeline  
> **Duration**: ~2 days  
> **Derived From**: [implementationPlan.md](./implementationPlan.md) · [architecture.md §3.1–§4](./architecture.md#31-document-loader)

---

## Overview

Phase 1 builds the offline ingestion pipeline: fetch → clean → chunk → embed → store. Evaluation focuses on **data quality, pipeline reliability, and idempotency**.

---

## Evaluation Categories

### 1. HTML Loader — Fetch & Extract

**Criteria**: All 12 Groww URLs are fetched successfully with clean text output.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-1.1.1 | All 12 URLs return HTTP 200 | Run loader against all URLs | 12/12 successful responses |
| E-1.1.2 | URL whitelist enforcement | Attempt to load `https://moneycontrol.com/...` | Rejected with "Domain not whitelisted" error |
| E-1.1.3 | Extracted text is non-empty for all URLs | Check `len(text) > 0` for each | All 12 produce non-empty text |
| E-1.1.4 | No HTML tags in extracted text | `re.search(r'<[a-z]+[^>]*>', text)` | No matches found |
| E-1.1.5 | No navigation/footer boilerplate | Manual spot-check: no "Download App", "About Groww", etc. | Clean content only |
| E-1.1.6 | Metadata attached correctly | Check each document's metadata dict | Has `source_url`, `scheme_name`, `document_type`, `fetch_date` |
| E-1.1.7 | Retry logic works on transient failure | Mock HTTP 500 response | Retries up to 3 times with backoff |
| E-1.1.8 | Timeout handling | Mock 60s delay | Fails gracefully after 30s timeout |
| E-1.1.9 | Graceful handling of single URL failure | Make 1 URL unreachable | Other 11 URLs still ingested successfully |

### 2. Text Pre-processing

**Criteria**: Raw text is cleaned and normalised without losing meaningful content.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-1.2.1 | HTML entities decoded | Check for `&amp;`, `&lt;`, `&#8377;`, etc. | All decoded to readable characters |
| E-1.2.2 | Excessive whitespace normalised | Check for `\n\n\n+` or `\s{3,}` | Max 2 consecutive newlines, no excessive spaces |
| E-1.2.3 | Financial symbols preserved | Check for `₹`, `%`, `.` in numbers | Currency and percentage symbols intact |
| E-1.2.4 | Table data preserved | Spot-check expense ratio, NAV tables | Tabular data is readable (not garbled) |
| E-1.2.5 | Empty lines between sections | Sections are visually separated | Readable text with logical structure |

### 3. Chunking Quality

**Criteria**: Chunks are correctly sized, overlapped, and metadata-enriched.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-1.3.1 | Chunk size within target range | Measure token count per chunk | 80% of chunks between 300–600 tokens |
| E-1.3.2 | Overlap between consecutive chunks | Compare adjacent chunk texts | ~100 tokens of overlap (±30 tokens) |
| E-1.3.3 | Tables preserved as single chunk | Find chunks containing tabular data | Tables not split mid-row |
| E-1.3.4 | Section boundaries respected | Check if chunks start/end near headings | Majority of splits at logical boundaries |
| E-1.3.5 | Metadata inheritance | Check every chunk's metadata | Every chunk has `source_url`, `scheme_name`, `document_type`, `fetch_date`, `chunk_index` |
| E-1.3.6 | Chunk count is reasonable | Count total chunks across 12 schemes | Between 50–500 total chunks (ballpark) |
| E-1.3.7 | No empty chunks | Check `len(chunk.text.strip()) > 0` | Zero empty chunks |
| E-1.3.8 | No duplicate chunks | Hash all chunk texts, check for collisions | Zero exact duplicates |

### 4. Embedding & Vector Store

**Criteria**: Embeddings are generated correctly and stored in ChromaDB with proper metadata.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-1.4.1 | ChromaDB collection created | `client.get_collection('mf_faq_v1')` | Collection exists, no errors |
| E-1.4.2 | Chunk count matches | `collection.count()` vs. chunker output count | Counts match exactly |
| E-1.4.3 | Embedding dimensions correct | `collection.get(include=['embeddings'])` | 384 dimensions (bge-small) |
| E-1.4.4 | Metadata stored with embeddings | `collection.get(include=['metadatas'])` | Every record has `source_url`, `scheme_name`, `fetch_date` |
| E-1.4.5 | Semantic search returns relevant results | Query "expense ratio HDFC Small Cap" | Top result is from HDFC Small Cap Fund |
| E-1.4.6 | Vector store persisted to disk | Restart Python, reload ChromaDB | Data survives restart |
| E-1.4.7 | All 12 schemes represented | `set(m['scheme_name'] for m in collection.get()['metadatas'])` | All 12 unique scheme names present |

### 5. Pipeline Reliability

**Criteria**: The ingestion script is robust, idempotent, and produces consistent results.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-1.5.1 | End-to-end script runs without errors | `python scripts/ingest.py --config data/corpus.yml --output data/vectorstore` | Exit code 0 |
| E-1.5.2 | Idempotency — running twice gives same result | Run ingestion twice, compare `collection.count()` | Same count both times (no duplicates) |
| E-1.5.3 | `--force` flag triggers full re-index | Run with `--force` | Collection recreated from scratch |
| E-1.5.4 | Logging output is clean and informative | Review stdout/stderr | Progress per URL, total chunks, timing |
| E-1.5.5 | Partial failure resilience | Make 2 URLs fail | Other 10 URLs ingested, 2 failures logged |

---

## Test Data & Queries

### Smoke Test Queries (post-ingestion, manual)

```python
import chromadb

client = chromadb.PersistentClient(path="data/vectorstore")
col = client.get_collection("mf_faq_v1")

# Basic search
results = col.query(query_texts=["expense ratio HDFC Small Cap Fund"], n_results=3)
for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
    print(f"Score: {1 - dist:.3f} | Scheme: {meta['scheme_name']}")
    print(f"  Text: {doc[:100]}...")
    print()
```

### Expected Results per Scheme

| Scheme | Expected Chunks | Key Content Present |
|--------|----------------|---------------------|
| HDFC Small Cap Fund | ≥ 3 | Expense ratio, exit load, NAV, fund category |
| HDFC Large Cap Fund | ≥ 3 | Expense ratio, exit load, NAV, benchmark |
| HDFC Mid Cap Fund | ≥ 3 | Expense ratio, exit load, NAV |
| HDFC Gold ETF FoF | ≥ 2 | Expense ratio, NAV, gold exposure |
| HDFC Multi Cap Fund | ≥ 3 | Expense ratio, exit load, allocation |
| HDFC BSE Sensex Index | ≥ 2 | Expense ratio, tracking error, benchmark |
| HDFC Short Term Opp. | ≥ 2 | Expense ratio, yield, duration |
| HDFC Focused Fund | ≥ 3 | Expense ratio, exit load, concentration |
| HDFC Nifty Next 50 | ≥ 2 | Expense ratio, tracking error, benchmark |
| HDFC Pharma & HC | ≥ 3 | Expense ratio, sector allocation |
| HDFC Balanced Advantage | ≥ 3 | Expense ratio, equity/debt split |
| HDFC Defence Fund | ≥ 2 | Expense ratio, sector focus |

---

## Scoring Rubric

| Rating | Criteria |
|--------|----------|
| ✅ **Pass** | All checks pass; all 12 schemes ingested with correct metadata |
| ⚠️ **Conditional Pass** | 10–11 schemes ingested; ≤ 3 non-critical checks fail |
| ❌ **Fail** | < 10 schemes ingested, OR vector store not persistent, OR duplicates on re-run |

---

> **Previous**: [eval-phase-0.md](./eval-phase-0.md) — Scaffold & Config  
> **Next**: [eval-phase-2.md](./eval-phase-2.md) — RAG Engine

# Evaluation Criteria — Phase 2: RAG Engine (Retrieval + Generation)

> **Phase**: 2 — RAG Engine  
> **Duration**: ~2 days  
> **Derived From**: [implementationPlan.md](./implementationPlan.md) · [architecture.md §3.5–§7](./architecture.md#35-retriever)

---

## Overview

Phase 2 builds the core RAG pipeline: query embedding → vector retrieval → LLM generation. Evaluation focuses on **retrieval accuracy, response quality, format compliance, and latency**.

---

## Evaluation Categories

### 1. Retrieval Accuracy

**Criteria**: The retriever returns relevant, correctly-scoped chunks for factual queries.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-2.1.1 | Scheme-specific query retrieves correct scheme | Query: "expense ratio of HDFC Small Cap Fund" | Top-1 chunk is from HDFC Small Cap Fund |
| E-2.1.2 | All 12 schemes are retrievable | 1 query per scheme (see test matrix below) | 12/12 return relevant top-1 chunk |
| E-2.1.3 | Top-k chunks are from the same scheme | Query about specific fund | ≥ 3 of top-5 chunks from queried scheme |
| E-2.1.4 | Relevance scores above threshold | Check similarity scores | Top-1 score ≥ 0.65 for supported queries |
| E-2.1.5 | Irrelevant query scores below threshold | Query: "What is the capital of France?" | All chunks score < 0.65 |
| E-2.1.6 | Metadata filtering works | Query "HDFC Mid Cap" with `scheme_name` filter | Only HDFC Mid Cap chunks returned |
| E-2.1.7 | Query normalisation works | Query: "EXPENSE RATIO hdfc small cap" (mixed case) | Same results as lowercase query |
| E-2.1.8 | Non-corpus scheme query | Query: "expense ratio of HDFC Flexi Cap Fund" | No chunks above threshold → "No info" response |

### 2. Response Format Compliance

**Criteria**: Every generated response strictly follows the mandated format from [architecture.md §7](./architecture.md#7-generation--response-pipeline).

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-2.2.1 | Response is ≤ 3 sentences | Count sentences in 10 sample responses | All responses have ≤ 3 sentences |
| E-2.2.2 | Response includes exactly 1 citation URL | Parse response for URLs | Exactly 1 URL present, from `groww.in` domain |
| E-2.2.3 | Response includes "Last updated" footer | Check for `"Last updated from sources:"` string | Footer present in all responses |
| E-2.2.4 | Citation URL is valid Groww URL | Validate URL format | URL matches one of the 12 corpus URLs |
| E-2.2.5 | Response is factual (grounded in context) | Manual review of 10 responses | No fabricated facts or hallucinations |
| E-2.2.6 | Response JSON schema matches spec | Validate against Pydantic model | Has `answer`, `citation`, `last_updated`, `query_type` fields |

### 3. Generation Quality

**Criteria**: Answers are accurate, concise, and grounded in retrieved context.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-2.3.1 | Answer contains the queried fact | Query expense ratio → response has a percentage | Factual content present |
| E-2.3.2 | Answer does not contain advisory language | Check for "should", "recommend", "best", "buy", "sell" | No advisory language |
| E-2.3.3 | Answer does not hallucinate numbers | Cross-check response values against source page | Values match source data |
| E-2.3.4 | "No information" fallback works | Query about non-corpus topic | Honest "I don't have that information" response |
| E-2.3.5 | Temperature produces consistent results | Same query 3 times | Responses are substantively identical |
| E-2.3.6 | Response language is English | Check all responses | 100% English responses |

### 4. Latency & Performance

**Criteria**: End-to-end response time is within acceptable bounds.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-2.4.1 | Embedding latency (query) | Time the query embedding step | < 500ms |
| E-2.4.2 | Vector search latency | Time the ChromaDB query | < 200ms |
| E-2.4.3 | LLM generation latency | Time the Groq API call | < 2000ms |
| E-2.4.4 | End-to-end latency | Time from query input to response output | < 3000ms |
| E-2.4.5 | Latency under repeated queries | Run 10 queries sequentially | No degradation (±20% variance) |

---

## Test Query Matrix

Run each query and validate the retrieval + generation output:

| # | Query | Target Scheme | Expected Fact Type | Pass if |
|---|-------|---------------|-------------------|---------|
| Q-1 | "What is the expense ratio of HDFC Small Cap Fund?" | Small Cap | Expense ratio (%) | Correct %, Groww URL citation |
| Q-2 | "What is the exit load for HDFC Large Cap Fund?" | Large Cap | Exit load | Mentions %, redemption period |
| Q-3 | "What is the minimum SIP amount for HDFC Mid Cap Fund?" | Mid Cap | Min SIP (₹) | Correct ₹ amount |
| Q-4 | "What is the NAV of HDFC Gold ETF Fund of Fund?" | Gold ETF FoF | NAV | Returns a NAV value |
| Q-5 | "What category does HDFC Multi Cap Fund belong to?" | Multi Cap | Category | "Multi Cap" or similar |
| Q-6 | "What benchmark does HDFC BSE Sensex Index Fund track?" | BSE Sensex Index | Benchmark | "BSE Sensex" or "S&P BSE Sensex" |
| Q-7 | "What is the fund type of HDFC Short Term Opportunities Fund?" | Short Term Opp. | Fund type | Debt / Short Duration |
| Q-8 | "How many stocks does HDFC Focused Fund hold?" | Focused Fund | Holdings count | A reasonable number |
| Q-9 | "What index does HDFC Nifty Next 50 Index Fund track?" | Nifty Next 50 | Benchmark | "Nifty Next 50" |
| Q-10 | "What sector does HDFC Pharma and Healthcare Fund invest in?" | Pharma & HC | Sector | Pharma / Healthcare |
| Q-11 | "What is the expense ratio of HDFC Balanced Advantage Fund?" | Balanced Advantage | Expense ratio | Correct % |
| Q-12 | "What is the investment objective of HDFC Defence Fund?" | Defence Fund | Objective | Defence/defence-related |

### Negative Test Queries

| # | Query | Expected Behaviour |
|---|-------|--------------------|
| N-1 | "What is the expense ratio of ICICI Blue Chip Fund?" | "I don't have that information" |
| N-2 | "What is the weather today?" | Below threshold → "No info" (guardrails in Phase 3) |
| N-3 | "" (empty string) | "Please enter a question" |
| N-4 | "asdfghjkl" (gibberish) | Below threshold → "No info" |

---

## Automated Evaluation Script

```python
"""Phase 2 Evaluation — RAG Engine"""
import time
from src.retrieval.retriever import retrieve
from src.generation.generator import generate

TEST_QUERIES = [
    ("What is the expense ratio of HDFC Small Cap Fund?", "HDFC Small Cap Fund"),
    ("What is the exit load for HDFC Large Cap Fund?", "HDFC Large Cap Fund"),
    ("What is the minimum SIP for HDFC Mid Cap Fund?", "HDFC Mid Cap Fund"),
    # ... add all 12
]

results = []
for query, expected_scheme in TEST_QUERIES:
    start = time.time()
    chunks = retrieve(query)
    response = generate(query, chunks)
    elapsed = time.time() - start

    top_scheme = chunks[0].metadata["scheme_name"] if chunks else "NONE"
    top_score = chunks[0].score if chunks else 0.0

    passed = (
        top_scheme == expected_scheme
        and top_score >= 0.65
        and len(response.answer.split(". ")) <= 4  # rough ≤3 sentence check
        and "groww.in" in response.citation.url
        and "Last updated" in response.answer
        and elapsed < 3.0
    )

    results.append({
        "query": query,
        "expected": expected_scheme,
        "got": top_scheme,
        "score": top_score,
        "latency": f"{elapsed:.2f}s",
        "passed": "✅" if passed else "❌"
    })
    print(f"{'✅' if passed else '❌'} [{elapsed:.2f}s] {query[:60]}... → {top_scheme}")

passed = sum(1 for r in results if r["passed"] == "✅")
print(f"\nResult: {passed}/{len(results)} passed")
```

---

## Scoring Rubric

| Rating | Criteria |
|--------|----------|
| ✅ **Pass** | ≥ 10/12 scheme queries return correct top-1 retrieval + valid response format |
| ⚠️ **Conditional Pass** | 8–9/12 pass; latency occasionally > 3s; minor format issues |
| ❌ **Fail** | < 8/12 pass, OR hallucination detected, OR "No info" for corpus queries |

---

> **Previous**: [eval-phase-1.md](./eval-phase-1.md) — Data Pipeline  
> **Next**: [eval-phase-3.md](./eval-phase-3.md) — Guardrails & Safety

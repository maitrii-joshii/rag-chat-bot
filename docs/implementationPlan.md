# Implementation Plan — RAG Mutual Fund FAQ Assistant

> **Version**: 1.0  
> **Last Updated**: 2026-08-05  
> **Status**: Draft  
> **Derived From**: [architecture.md](./architecture.md) · [context.md](./context.md)

---

## Overview

This document outlines a **6-phase implementation plan** for building the RAG Mutual Fund FAQ Assistant — a facts-only Q&A system for **HDFC Mutual Fund** schemes. Each phase is self-contained with clear deliverables, exit criteria, and estimated effort.

### Phasing Strategy

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
Scaffold     Data        RAG         Guardrails   Frontend    Deploy &
& Config     Pipeline    Engine      & Safety     & API       Automate
(0.5 day)    (2 days)    (2 days)    (1 day)      (1.5 days)  (1 day)
                                                              ─────────
                                                              ~8 days
```

### Target AMC & Schemes

| AMC | Schemes | Data Source |
|-----|---------|-------------|
| **HDFC Mutual Fund** | 12 schemes (see [corpus details](#appendix-a--hdfc-scheme-registry)) | Groww scheme pages |

---

## Phase 0 — Project Scaffold & Configuration

> **Goal**: Establish project structure, dependency management, and configuration files so that all subsequent phases have a clean foundation.

### Duration: ~0.5 day

### Tasks

| # | Task | File(s) | Notes |
|---|------|---------|-------|
| 0.1 | Initialise the directory structure as per [architecture.md §12](./architecture.md#12-directory-structure) | All directories + `__init__.py` files | See tree below |
| 0.2 | Create `requirements.txt` with all pinned dependencies | `requirements.txt` | See dependency list |
| 0.3 | Create `.env.example` with all env vars documented | `.env.example` | Based on [architecture.md §14](./architecture.md#14-configuration--environment) |
| 0.4 | Create `data/corpus.yml` with HDFC scheme registry | `data/corpus.yml` | 12 schemes, 12 Groww URLs |
| 0.5 | Create `data/holidays.json` for 2026 | `data/holidays.json` | NSE/BSE + national holidays |
| 0.6 | Create `.gitignore` | `.gitignore` | Exclude `.env`, `__pycache__`, `data/vectorstore/`, etc. |
| 0.7 | Set up Python virtual environment | — | `python -m venv venv` |

### Directory Structure (to create)

```
rag-chat-bot/
├── .github/workflows/
├── docs/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   ├── chunker.py
│   │   └── embedder.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── prompts.py
│   │   └── postprocessor.py
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── pii_detector.py
│   │   ├── intent_classifier.py
│   │   └── refusal_handler.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   └── ui/
│       ├── index.html
│       ├── style.css
│       └── script.js
├── data/
│   ├── corpus.yml
│   ├── holidays.json
│   └── vectorstore/
├── scripts/
│   ├── ingest.py
│   └── evaluate.py
├── tests/
│   ├── test_guardrails.py
│   ├── test_retriever.py
│   └── test_refusal.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Key Dependencies (`requirements.txt`)

```
# Core
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
python-dotenv>=1.0.0
pyyaml>=6.0.1

# RAG Pipeline
langchain>=0.2.0
langchain-community>=0.2.0
chromadb>=0.5.0
sentence-transformers>=3.0.0

# LLM
groq>=0.9.0

# Document Loading
beautifulsoup4>=4.12.0
requests>=2.32.0
pdfplumber>=0.11.0

# Guardrails
regex>=2024.5.0

# Testing
pytest>=8.2.0
httpx>=0.27.0
```

### Exit Criteria

- [ ] All directories and placeholder files exist
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `.env.example` documents every required variable
- [ ] `data/corpus.yml` contains all 12 HDFC schemes with Groww URLs
- [ ] `git init` + initial commit complete

---

## Phase 1 — Data Ingestion Pipeline

> **Goal**: Build the offline pipeline that fetches content from Groww scheme pages, cleans/chunks the text, generates embeddings, and stores them in ChromaDB.

### Duration: ~2 days

### Dependencies: Phase 0 complete

### Tasks

| # | Task | File(s) | Architecture Ref |
|---|------|---------|-----------------|
| 1.1 | **HTML Loader** — Fetch and extract text from Groww scheme pages using BeautifulSoup4 | `src/ingestion/loader.py` | [§3.1](./architecture.md#31-document-loader) |
| 1.2 | **URL Whitelist** — Enforce domain whitelist (`groww.in`, `hdfcfund.com`, `amfiindia.com`, `sebi.gov.in`) | `src/ingestion/loader.py` | [§3.1](./architecture.md#31-document-loader) |
| 1.3 | **Text Pre-processor** — Clean HTML artefacts, strip boilerplate, normalise whitespace | `src/ingestion/preprocessor.py` | [§4 Pipeline](./architecture.md#4-data-pipeline-architecture) |
| 1.4 | **Chunker** — Section-aware splitting (~500 tokens, ~100 overlap), table preservation | `src/ingestion/chunker.py` | [§3.2](./architecture.md#32-text-splitter--chunker) |
| 1.5 | **Metadata Enrichment** — Attach `source_url`, `scheme_name`, `document_type`, `fetch_date`, `chunk_index` | `src/ingestion/chunker.py` | [§3.4 Schema](./architecture.md#34-vector-store) |
| 1.6 | **Embedder** — Generate BGE embeddings (`bge-small-en-v1.5`) and upsert into ChromaDB | `src/ingestion/embedder.py` | [§3.3](./architecture.md#33-embedding-model), [§3.4](./architecture.md#34-vector-store) |
| 1.7 | **Ingestion Script** — CLI entry point that orchestrates the full pipeline | `scripts/ingest.py` | [§5.3](./architecture.md#53-workflow-definition) |
| 1.8 | **Corpus Config Loader** — Parse `data/corpus.yml` and feed URLs to the loader | `scripts/ingest.py` | [§4.1](./architecture.md#41-corpus-registry-corpusyml) |

### Sub-task Detail: HTML Loader (1.1)

The Groww scheme pages contain structured data (NAV, expense ratio, exit load, holdings, etc.) rendered as HTML. The loader must:

1. Send HTTP GET requests with appropriate headers (User-Agent, timeout)
2. Parse the HTML response with BeautifulSoup4
3. Extract meaningful text sections (overview, key facts table, fund details)
4. Discard navigation, footer, ads, and other boilerplate
5. Return structured output: `{ "text": str, "metadata": dict }`

```python
# Pseudocode
def load_url(url: str, scheme_name: str) -> Document:
    response = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract relevant sections, strip boilerplate
    text = extract_scheme_content(soup)
    metadata = {
        "source_url": url,
        "scheme_name": scheme_name,
        "document_type": "scheme_page",
        "fetch_date": datetime.now().isoformat()
    }
    return Document(text=text, metadata=metadata)
```

### Sub-task Detail: Chunker (1.4)

```
Raw Document (~2000–5000 tokens)
        │
        ▼
┌────────────────────────────────────┐
│  Split at section boundaries       │
│  (headings, double newlines)       │
├────────────────────────────────────┤
│  Each chunk: ~500 tokens           │
│  Overlap: ~100 tokens              │
│  Tables → kept as single chunk     │
│  Each chunk inherits parent meta   │
└────────────────────────────────────┘
```

### Verification

```bash
# Run the full ingestion pipeline
python scripts/ingest.py --config data/corpus.yml --output data/vectorstore

# Verify vector store was populated
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/vectorstore')
col = client.get_collection('mf_faq_v1')
print(f'Total chunks: {col.count()}')
"
```

### Exit Criteria

- [ ] All 12 Groww URLs are fetched successfully
- [ ] Text is cleaned (no HTML tags, no boilerplate)
- [ ] Chunks are ~500 tokens with ~100 overlap
- [ ] ChromaDB collection has chunks with correct metadata (`source_url`, `scheme_name`, `fetch_date`)
- [ ] `scripts/ingest.py` runs end-to-end without errors
- [ ] Running ingestion twice does not create duplicate chunks (idempotent)

---

## Phase 2 — RAG Engine (Retrieval + Generation)

> **Goal**: Build the core query pipeline — embed the user's question, retrieve relevant chunks, and generate a factual, cited answer via Groq LLM.

### Duration: ~2 days

### Dependencies: Phase 1 complete (vector store populated)

### Tasks

| # | Task | File(s) | Architecture Ref |
|---|------|---------|-----------------|
| 2.1 | **Retriever** — Embed user query (BGE), search ChromaDB (cosine, top-k=5), apply score threshold (≥0.65) | `src/retrieval/retriever.py` | [§3.5](./architecture.md#35-retriever), [§6](./architecture.md#6-retrieval-strategy) |
| 2.2 | **Query Pre-processing** — Lowercase normalisation, scheme name canonicalisation | `src/retrieval/retriever.py` | [§6.1](./architecture.md#61-query-processing) |
| 2.3 | **Metadata Pre-filtering** — If query mentions a specific fund, filter by `scheme_name` before vector search | `src/retrieval/retriever.py` | [§6.2](./architecture.md#62-retrieval-modes) |
| 2.4 | **System Prompt** — Define the facts-only system prompt with response format rules | `src/generation/prompts.py` | [§3.6](./architecture.md#36-generator-llm) |
| 2.5 | **Prompt Template** — Context assembly template (chunks + metadata + query) | `src/generation/prompts.py` | [§3.6](./architecture.md#36-generator-llm) |
| 2.6 | **Generator** — Invoke Groq API (`openai/gpt-oss-120b` with `qwen/qwen3.6-27b` fallback, temp=0.1, max_tokens=150) | `src/generation/generator.py` | [§3.6](./architecture.md#36-generator-llm) |
| 2.7 | **Post-processor** — Validate response (≤3 sentences, citation present, footer present) | `src/generation/postprocessor.py` | [§7.1](./architecture.md#71-response-construction-flow) |
| 2.8 | **"No Information" fallback** — Handle case where no chunks pass the relevance threshold | `src/generation/generator.py` | [§6.3](./architecture.md#63-relevance-threshold) |

### Retrieval Flow

```
User Query: "What is the expense ratio of HDFC Small Cap Fund?"
    │
    ▼
┌──────────────────────────────────┐
│ 1. Normalise query               │
│ 2. Detect scheme name → filter   │
│ 3. Embed query (BGE)             │
│ 4. Vector search (top-5, ≥0.65)  │
│ 5. Return ranked chunks + meta   │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│ 6. Assemble prompt (system +     │
│    context chunks + user query)  │
│ 7. Call Groq LLM                 │
│ 8. Validate response format      │
│ 9. Return answer + citation      │
└──────────────────────────────────┘
```

### System Prompt (from architecture)

```
You are a facts-only mutual fund FAQ assistant. You answer ONLY using the
provided context. You MUST:
  1. Respond in ≤ 3 sentences using only information from the context.
  2. Include exactly 1 source citation URL from the context metadata.
  3. End with: "Last updated from sources: <date>"
  4. REFUSE any advisory, comparative, or speculative questions politely.
  5. NEVER provide investment advice, performance comparisons, or opinions.
  6. If the context does not contain the answer, say so honestly.
```

### Verification

```bash
# Test the RAG pipeline end-to-end (manual)
python -c "
from src.retrieval.retriever import retrieve
from src.generation.generator import generate

chunks = retrieve('What is the expense ratio of HDFC Small Cap Fund?')
response = generate('What is the expense ratio of HDFC Small Cap Fund?', chunks)
print(response)
"
```

### Test Queries

| Query | Expected Behaviour |
|-------|-------------------|
| "What is the expense ratio of HDFC Small Cap Fund?" | Factual answer + Groww URL citation |
| "What is the exit load for HDFC Large Cap Fund?" | Factual answer + Groww URL citation |
| "What is the minimum SIP for HDFC Mid Cap Fund?" | Factual answer + Groww URL citation |
| "Tell me about a fund not in our corpus" | "I don't have that information" response |
| "What is the weather today?" | Out-of-scope (handled in Phase 3) |

### Exit Criteria

- [ ] Retriever returns relevant chunks for factual queries about all 12 HDFC schemes
- [ ] Generator produces ≤3-sentence answers with citation URL and "Last updated" footer
- [ ] Relevance threshold (0.65) correctly filters irrelevant chunks
- [ ] "No information" fallback works when no relevant chunks found
- [ ] End-to-end latency < 3 seconds (retrieval + generation)

---

## Phase 3 — Guardrails & Safety Layer

> **Goal**: Implement pre-generation and post-generation safety checks — PII detection, advisory intent classification, and refusal handling.

### Duration: ~1 day

### Dependencies: Phase 2 complete (RAG engine functional)

### Tasks

| # | Task | File(s) | Architecture Ref |
|---|------|---------|-----------------|
| 3.1 | **PII Detector** — Regex patterns for PAN, Aadhaar, phone, email, bank account | `src/guardrails/pii_detector.py` | [§8.3](./architecture.md#83-pii-detection-patterns-regex) |
| 3.2 | **Advisory Intent Classifier** — Keyword-based detection of advisory, comparison, prediction, buy/sell queries | `src/guardrails/intent_classifier.py` | [§8.1](./architecture.md#81-classification-taxonomy), [§8.2](./architecture.md#82-advisory-detection-patterns) |
| 3.3 | **Out-of-Scope Detector** — Detect non-mutual-fund queries (topic drift) | `src/guardrails/intent_classifier.py` | [§3.7](./architecture.md#37-guardrails--refusal-engine) |
| 3.4 | **Refusal Handler** — Generate polite refusal with AMFI fallback link | `src/guardrails/refusal_handler.py` | [§7.3](./architecture.md#73-refusal-response-schema) |
| 3.5 | **Post-Generation Validation** — Scan LLM output for advisory language, PII, missing citations | `src/generation/postprocessor.py` | [§3.7 Post-gen](./architecture.md#37-guardrails--refusal-engine) |
| 3.6 | **Unit Tests** — Test all guardrail patterns with positive and negative examples | `tests/test_guardrails.py`, `tests/test_refusal.py` | — |

### PII Patterns

| PII Type | Regex | Example Match |
|----------|-------|---------------|
| PAN | `[A-Z]{5}[0-9]{4}[A-Z]{1}` | `ABCDE1234F` |
| Aadhaar | `[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}` | `1234 5678 9012` |
| Phone | `(\+91[\s-]?)?[6-9][0-9]{9}` | `+91 9876543210` |
| Email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | `user@email.com` |
| Bank Account | `[0-9]{9,18}` (context-aware) | `123456789012` |

### Advisory Patterns

| Category | Keywords / Phrases |
|----------|--------------------|
| Direct advice | "should I invest", "recommend a fund", "is it a good fund" |
| Comparison | "which is better", "compare X and Y", "best fund for" |
| Prediction | "will it give returns", "future performance", "expected NAV" |
| Buy/Sell | "should I buy", "time to sell", "entry point" |

### Query Classification Flow

```
User Query
    │
    ├──► PII detected?     → Block & warn (never reaches RAG)
    ├──► Advisory intent?  → Polite refusal + AMFI link
    ├──► Out of scope?     → Polite refusal
    └──► Factual           → Proceed to retrieval → generation
```

### Verification

```bash
pytest tests/test_guardrails.py -v
pytest tests/test_refusal.py -v
```

### Test Cases

| Input | Expected Classification | Expected Action |
|-------|------------------------|-----------------|
| "What is the expense ratio of HDFC Fund?" | Factual | Proceed to RAG |
| "Should I invest in HDFC Small Cap?" | Advisory | Polite refusal |
| "Which is better — HDFC Small Cap or Mid Cap?" | Comparison | Polite refusal |
| "My PAN is ABCDE1234F" | PII detected | Block & warn |
| "What is the weather today?" | Out of scope | Polite refusal |
| "Will HDFC Defence Fund give 20% returns?" | Prediction | Polite refusal |

### Exit Criteria

- [ ] PII detection catches all 5 PII types with zero false negatives on test set
- [ ] Advisory classifier correctly routes advisory/comparison/prediction queries to refusal
- [ ] Refusal responses are polite, include AMFI fallback link, and have "Last updated" footer
- [ ] Post-generation validator catches advisory language in LLM output
- [ ] All guardrail unit tests pass
- [ ] No PII is ever logged or stored

---

## Phase 4 — API & Frontend

> **Goal**: Expose the RAG engine via FastAPI endpoints and build the minimal chat UI.

### Duration: ~1.5 days

### Dependencies: Phase 3 complete (guardrails functional)

### Tasks

| # | Task | File(s) | Architecture Ref |
|---|------|---------|-----------------|
| 4.1 | **Pydantic Schemas** — Request/response models for `/api/chat`, `/api/health`, `/api/examples` | `src/api/schemas.py` | [§9.1](./architecture.md#91-api-endpoints) |
| 4.2 | **API Routes** — Implement `POST /api/chat`, `GET /api/health`, `GET /api/examples` | `src/api/routes.py` | [§9.1](./architecture.md#91-api-endpoints) |
| 4.3 | **FastAPI App** — Application entry point with CORS, middleware, static file serving | `src/main.py` | [§11 Tech Stack](./architecture.md#11-technology-stack) |
| 4.4 | **Chat Orchestrator** — Wire guardrails → retriever → generator into a single `/api/chat` flow | `src/api/routes.py` | [§10.2 Query Flow](./architecture.md#102-query-flow-online) |
| 4.5 | **Rate Limiting** — Basic rate limiting on `/api/chat` | `src/main.py` | [§2 API Gateway](./architecture.md#2-high-level-architecture) |
| 4.6 | **Chat UI — HTML** — Layout with disclaimer banner, welcome message, example questions, chat area, input | `src/ui/index.html` | [§9.2](./architecture.md#92-ui-components) |
| 4.7 | **Chat UI — CSS** — Styling (clean, minimal, responsive) | `src/ui/style.css` | [§9.2](./architecture.md#92-ui-components) |
| 4.8 | **Chat UI — JS** — Fetch API integration, example question click handlers, response rendering | `src/ui/script.js` | [§9.2](./architecture.md#92-ui-components) |

### API Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| `POST` | `/api/chat` | `{ "query": "...", "session_id": "..." }` | `{ "answer": "...", "citation": {...}, "last_updated": "...", "query_type": "..." }` |
| `GET` | `/api/health` | — | `{ "status": "healthy", "vectorstore_chunks": N }` |
| `GET` | `/api/examples` | — | `{ "examples": ["...", "...", "..."] }` |

### UI Layout

```
┌──────────────────────────────────────────────────┐
│  ⚠️  Facts-only. No investment advice.            │  ← Disclaimer
├──────────────────────────────────────────────────┤
│                                                  │
│  👋 Welcome! I'm your HDFC Mutual Fund FAQ       │
│  Assistant. Ask me factual questions about       │
│  HDFC mutual fund schemes.                       │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ What is the expense ratio of HDFC Small Cap│  │  ← Clickable
│  │ What is the exit load for HDFC Large Cap   │  │     examples
│  │ What is the min SIP for HDFC Mid Cap       │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │           Chat History Area                │  │  ← Messages
│  │                                            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────┐  ┌──────────┐ │
│  │  Type your question...       │  │   Send   │ │  ← Input
│  └──────────────────────────────┘  └──────────┘ │
└──────────────────────────────────────────────────┘
```

### Verification

```bash
# Start the dev server
uvicorn src.main:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/api/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expense ratio of HDFC Small Cap Fund?"}'

# Test examples endpoint
curl http://localhost:8000/api/examples

# Open UI in browser
# http://localhost:8000
```

### Exit Criteria

- [ ] `POST /api/chat` returns correct JSON response for factual queries
- [ ] `POST /api/chat` returns refusal response for advisory queries
- [ ] `POST /api/chat` blocks queries containing PII
- [ ] `GET /api/health` returns healthy status with chunk count
- [ ] `GET /api/examples` returns 3 example questions
- [ ] Chat UI renders correctly in Chrome/Firefox
- [ ] Example questions are clickable and trigger queries
- [ ] Disclaimer banner is always visible
- [ ] Response displays answer + citation link + "Last updated" footer
- [ ] UI is responsive (works on mobile and desktop viewports)

---

## Phase 5 — Deployment, Automation & Polish

> **Goal**: Deploy frontend to Vercel, backend to Railway, set up the GitHub Actions ingestion scheduler, write tests, and finalise documentation.

### Duration: ~1 day

### Dependencies: Phase 4 complete (API + UI working locally)

### Part A — Deployment

| # | Task | File(s) / Platform | Architecture Ref |
|---|------|---------------------|-----------------|
| 5.1 | **Railway Setup** — Deploy FastAPI backend with persistent volume for ChromaDB | Railway dashboard | [§15.2](./architecture.md#152-production-vercel--railway) |
| 5.2 | **Railway Secrets** — Configure `GROQ_API_KEY` and other env vars | Railway dashboard | [§15.4](./architecture.md#154-platform-configuration) |
| 5.3 | **Vercel Setup** — Deploy static frontend (`src/ui/`) with `BACKEND_URL` env var | Vercel dashboard | [§15.2](./architecture.md#152-production-vercel--railway) |
| 5.4 | **CORS Configuration** — Allow Vercel domain on Railway backend | `src/main.py` | — |
| 5.5 | **Smoke Test** — Verify end-to-end on production (Vercel → Railway → Groq) | — | — |

### Part B — GitHub Actions Scheduler

| # | Task | File(s) | Architecture Ref |
|---|------|---------|-----------------|
| 5.6 | **Weekday Ingestion Workflow** — Cron `0 5 * * 1-6` (Mon–Sat, 10:30 AM IST) | `.github/workflows/weekday-ingest.yml` | [§5](./architecture.md#5-scheduler--automated-ingestion-github-actions) |
| 5.7 | **Holiday Check Job** — Read `data/holidays.json`, skip on holidays | `.github/workflows/weekday-ingest.yml` | [§5.3](./architecture.md#53-workflow-definition) |
| 5.8 | **Auto-commit Vector Store** — Commit updated ChromaDB data on change | `.github/workflows/weekday-ingest.yml` | [§5.3](./architecture.md#53-workflow-definition) |
| 5.9 | **Failure Notification** — Create GitHub Issue on ingestion failure | `.github/workflows/weekday-ingest.yml` | [§5.6](./architecture.md#56-failure-handling) |

### Part C — Testing & Documentation

| # | Task | File(s) | Notes |
|---|------|---------|-------|
| 5.10 | **Retriever Tests** — Test retrieval accuracy across all 12 schemes | `tests/test_retriever.py` | At least 2 queries per scheme |
| 5.11 | **Evaluation Script** — Batch test with predefined Q&A pairs | `scripts/evaluate.py` | Gold-standard test set |
| 5.12 | **README.md** — Setup instructions, AMC & schemes, architecture overview, limitations | `README.md` | Per [context.md §11](./context.md#11-expected-deliverables) |
| 5.13 | **Final Review** — Code cleanup, logging, error messages | All files | — |

### Deployment Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION                                      │
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────────────┐   │
│  │      VERCEL          │  HTTP   │         RAILWAY              │   │
│  │  src/ui/ (static)    │ ──────► │  FastAPI + ChromaDB + BGE   │   │
│  │  Edge CDN            │         │  Groq API client            │   │
│  └─────────────────────┘         └─────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  GitHub Actions — Weekday Ingestion (Mon–Sat, 10:30 AM IST) │   │
│  │  Holiday-aware · Auto-commit · Failure notification         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Exit Criteria

- [ ] Backend live on Railway and responding to API calls
- [ ] Frontend live on Vercel and communicating with Railway backend
- [ ] CORS configured correctly (no browser errors)
- [ ] GitHub Actions workflow passes on manual dispatch
- [ ] Holiday check correctly skips on holiday dates
- [ ] Auto-commit works when vector store changes
- [ ] Failure notification creates a GitHub Issue on error
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] README.md is complete with setup instructions and limitations
- [ ] End-to-end smoke test passes on production

---

## Summary — Phase Timeline

| Phase | Name | Duration | Key Output |
|-------|------|----------|------------|
| **0** | Scaffold & Config | 0.5 day | Project structure, deps, config files |
| **1** | Data Pipeline | 2 days | Loader → Chunker → Embedder → ChromaDB |
| **2** | RAG Engine | 2 days | Retriever + Generator (Groq) → factual answers |
| **3** | Guardrails & Safety | 1 day | PII detector, advisory classifier, refusal handler |
| **4** | API & Frontend | 1.5 days | FastAPI endpoints + chat UI |
| **5** | Deploy & Automate | 1 day | Vercel + Railway + GitHub Actions scheduler |
| | **Total** | **~8 days** | |

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Groww blocks scraping (rate limit / CAPTCHA) | High — no data | Medium | Respectful rate limiting, User-Agent headers, cache responses, fallback to official HDFC AMC site |
| Groq free tier rate limits hit | Medium — degraded UX | Low (MVP) | Response caching for frequent queries, queue + retry |
| BGE embedding quality insufficient | Medium — poor retrieval | Low | Switch to `bge-large-en-v1.5` or hybrid (BM25 + vector) search |
| ChromaDB corruption on Railway | High — total data loss | Low | Git-committed vector store as backup, re-ingestion script |
| Advisory false positives | Low — factual query refused | Medium | Narrow keyword patterns, allow borderline queries through |
| Groww page HTML structure changes | High — loader breaks | Medium | Robust selectors, health-check alerts, manual review |

---

## Appendix A — HDFC Scheme Registry

| # | Scheme Name | Category | Groww URL |
|---|-------------|----------|-----------|
| 1 | HDFC Small Cap Fund - Direct Growth | Small-Cap | `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` |
| 2 | HDFC Gold ETF Fund of Fund - Direct Plan Growth | Gold / FoF | `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth` |
| 3 | HDFC Multi Cap Fund - Direct Growth | Multi-Cap | `https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth` |
| 4 | HDFC Large Cap Fund - Direct Growth | Large-Cap | `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` |
| 5 | HDFC Mid Cap Fund - Direct Growth | Mid-Cap | `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth` |
| 6 | HDFC BSE Sensex Index Fund - Direct Growth | Index | `https://groww.in/mutual-funds/hdfc-bse-sensex-index-fund-direct-growth` |
| 7 | HDFC Short Term Opportunities Fund - Direct Growth | Debt / Short Duration | `https://groww.in/mutual-funds/hdfc-short-term-opportunities-fund-direct-growth` |
| 8 | HDFC Focused Fund - Direct Growth | Focused | `https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth` |
| 9 | HDFC Nifty Next 50 Index Fund - Direct Growth | Index | `https://groww.in/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth` |
| 10 | HDFC Pharma and Healthcare Fund - Direct Growth | Sectoral / Thematic | `https://groww.in/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth` |
| 11 | HDFC Balanced Advantage Fund - Direct Growth | Hybrid / Dynamic AA | `https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth` |
| 12 | HDFC Defence Fund - Direct Growth | Sectoral / Thematic | `https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth` |

---

> **Document maintained by**: RAG Chat Bot development team  
> **Next review**: After Phase 0 completion and before Phase 1 kickoff

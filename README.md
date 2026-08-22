# RAG Mutual Fund FAQ Assistant

**Project Link**: [https://rag-chat-bot-lac.vercel.app/](https://rag-chat-bot-lac.vercel.app/)

> A facts-only Q&A chatbot for **HDFC Mutual Fund** schemes — powered by a full RAG (Retrieval-Augmented Generation) pipeline built with ChromaDB, BGE embeddings, and the Groq LLM API.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?logo=vercel&logoColor=white)](https://rag-chat-bot-lac.vercel.app/)
[![Backend API](https://img.shields.io/badge/Backend%20API-Railway-5C2096?logo=railway&logoColor=white)](https://rag-chat-bot-production.up.railway.app/api/health)
[![Tests](https://img.shields.io/badge/Tests-16%20passed-brightgreen?logo=pytest)](tests/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

This assistant answers **factual questions** about 12 HDFC Mutual Fund schemes — NAV, expense ratio, exit load, minimum SIP, fund category, benchmark, and more. It is powered by a full offline-first RAG pipeline:

1. **Scrape** — Groww scheme pages are fetched and cleaned.
2. **Chunk & Embed** — Text is chunked and embedded using `BAAI/bge-small-en-v1.5`.
3. **Store** — Embeddings are persisted in a ChromaDB vector store.
4. **Retrieve** — User queries are embedded and matched via cosine similarity.
5. **Generate** — Relevant chunks are passed to Groq's LLM (`openai/gpt-oss-120b`, fallback: `qwen/qwen3.6-27b`) to produce a cited, factual answer.
6. **Guard** — PII detection and advisory-intent classification block unsafe or out-of-scope queries.

The assistant **never** provides investment advice, performance comparisons, or predictions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PRODUCTION ARCHITECTURE                              │
│                                                                                 │
│  ┌─────────────────────┐  HTTPS  ┌─────────────────────────────────────────┐   │
│  │    VERCEL (CDN)      │ ──────► │           RAILWAY (Backend)             │   │
│  │  src/ui/ (static)    │         │  FastAPI + ChromaDB + BGE + Groq API   │   │
│  └─────────────────────┘         └─────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │         GitHub Actions — Weekday Scheduler (Mon–Sat, 10:30 AM IST)      │   │
│  │   Holiday-aware · POST /api/admin/ingest · Verify health · Issue alert  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

Query Pipeline (per request):

  User Query
      │
      ▼
  Guardrails ──► PII Detected?   → Block (pii_blocked)
      │     └──► Advisory query? → Polite Refusal
      │
      ▼ (factual intent only)
  Retriever  ──► BGE embed query → ChromaDB cosine search → top-k chunks (≥ 0.65)
      │
      ▼
  Generator  ──► Groq LLM (openai/gpt-oss-120b / fallback: qwen/qwen3.6-27b) + retrieved context
      │
      ▼
  Post-processor ──► Validate output, extract citation, strip advisory language
      │
      ▼
  Response   ──► { answer, citation { url, scheme_name, fetch_date }, last_updated }
```

Full architecture details: [`docs/architecture.md`](docs/architecture.md)

---

## HDFC Schemes Covered

| # | Scheme | Category |
|---|--------|----------|
| 1 | HDFC Small Cap Fund - Direct Growth | Small-Cap |
| 2 | HDFC Gold ETF Fund of Fund - Direct Plan Growth | Gold / FoF |
| 3 | HDFC Multi Cap Fund - Direct Growth | Multi-Cap |
| 4 | HDFC Large Cap Fund - Direct Growth | Large-Cap |
| 5 | HDFC Mid Cap Fund - Direct Growth | Mid-Cap |
| 6 | HDFC BSE Sensex Index Fund - Direct Growth | Index |
| 7 | HDFC Short Term Opportunities Fund - Direct Growth | Debt / Short Duration |
| 8 | HDFC Focused Fund - Direct Growth | Focused |
| 9 | HDFC Nifty Next 50 Index Fund - Direct Growth | Index |
| 10 | HDFC Pharma and Healthcare Fund - Direct Growth | Sectoral / Thematic |
| 11 | HDFC Balanced Advantage Fund - Direct Growth | Hybrid / Dynamic AA |
| 12 | HDFC Defence Fund - Direct Growth | Sectoral / Thematic |

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Embedding | `BAAI/bge-small-en-v1.5` (sentence-transformers) | 384-dim, cosine similarity |
| Vector Store | ChromaDB (persistent) | Score threshold ≥ 0.65 |
| LLM | Groq API — `openai/gpt-oss-120b` (fallback: `qwen/qwen3.6-27b`) | Via REST API |
| Framework | FastAPI + Uvicorn | ASGI, async |
| Frontend | Vanilla HTML / CSS / JS | No framework needed |
| Scheduler | GitHub Actions cron | Mon–Sat, 10:30 AM IST |
| Backend Hosting | Railway | Docker, persistent volume |
| Frontend Hosting | Vercel | Edge CDN, zero-config |

---

## Project Structure

```
rag-chat-bot/
├── .github/
│   └── workflows/
│       └── weekday-ingest.yml  # Cron scheduler (Mon–Sat 10:30 AM IST)
├── docs/
│   ├── architecture.md         # Full system architecture
│   ├── context.md              # Project brief and constraints
│   └── implementationPlan.md   # Phase-by-phase implementation plan
├── src/
│   ├── main.py                 # FastAPI app entry point + CORS + rate limiting
│   ├── api/
│   │   ├── routes.py           # /api/chat, /api/health, /api/examples, /api/admin/ingest
│   │   └── schemas.py          # Pydantic request/response models
│   ├── ingestion/
│   │   ├── loader.py           # Groww page fetcher + HTML parser
│   │   ├── preprocessor.py     # Text cleaner
│   │   ├── chunker.py          # Recursive text splitter (~500 tokens, 100 overlap)
│   │   └── embedder.py         # BGE encoder + ChromaDB writer
│   ├── retrieval/
│   │   └── retriever.py        # BGE query embed + ChromaDB cosine search + pre-filter
│   ├── generation/
│   │   ├── generator.py        # Groq LLM client + response generation
│   │   ├── prompts.py          # System prompt + citation formatter
│   │   └── postprocessor.py    # Output validator + last_updated extractor
│   ├── guardrails/
│   │   ├── pii_detector.py     # Regex-based PII detection
│   │   ├── intent_classifier.py # FACTUAL / ADVISORY / COMPARISON / OOS classifier
│   │   └── refusal_handler.py  # Polite refusal response builder
│   └── ui/
│       ├── index.html          # Chat UI layout
│       ├── style.css           # Dark theme, glassmorphism, responsive
│       ├── script.js           # Fetch API integration, streaming UX
│       └── vercel.json         # Rewrites /api/* → Railway backend
├── data/
│   ├── corpus.yml              # Scheme registry (12 HDFC schemes + Groww URLs)
│   ├── holidays.json           # 2026 NSE/BSE + national holidays
│   └── vectorstore/            # ChromaDB persistent store (gitignored)
├── scripts/
│   ├── ingest.py               # Offline ingestion CLI (run once or via cron)
│   └── evaluate.py             # Batch evaluation: Hit Rate, Coverage, Refusal Rate
├── tests/
│   └── test_retriever.py       # 16 unit tests — all 12 schemes + core logic
├── Dockerfile                  # Railway Docker build
├── railway.toml                # Railway deploy config
├── .env.example                # Environment variable template
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Pinned Python dependencies
└── README.md
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com)

### 1. Clone & create virtual environment

```bash
git clone https://github.com/maitrii-joshii/rag-chat-bot.git
cd rag-chat-bot

python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env — set GROQ_API_KEY=your-key-here
```

### 4. Run the ingestion pipeline

```bash
python scripts/ingest.py --config data/corpus.yml --output data/vectorstore
```

This fetches all 12 Groww scheme pages, chunks the text, and embeds it into ChromaDB. Takes ~1–2 minutes on first run (downloads BGE model).

### 5. Start the API server

```bash
uvicorn src.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## Cloud Deployment

The app uses a split-stack architecture: **Vercel** for the static frontend and **Railway** for the Python backend.

### Backend — Railway

1. Create a new project on [railway.com](https://railway.com) and import this GitHub repo.
2. In Railway → **Variables**, set:
   ```
   GROQ_API_KEY=<your-key>
   ALLOWED_ORIGINS=https://<your-vercel-url>
   ```
3. Add a **Volume** and mount it at `/app/data` (persists ChromaDB across deploys).
4. Railway auto-builds using the [`Dockerfile`](Dockerfile). Once live, trigger initial ingestion:
   ```powershell
   Invoke-RestMethod -Uri "https://<railway-url>/api/admin/ingest" -Method Post
   ```

### Frontend — Vercel

1. Create a new project on [vercel.com](https://vercel.com) and import this GitHub repo.
2. Set the **Root Directory** to `src/ui`.
3. Click **Deploy**. Vercel auto-rewrites `/api/*` requests to Railway via [`src/ui/vercel.json`](src/ui/vercel.json).

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Submit a factual query, get an answer + citation |
| `GET` | `/api/health` | Health check + vector store chunk count |
| `GET` | `/api/examples` | Return 3 example questions for the UI |
| `POST` | `/api/admin/ingest` | Trigger background ingestion (used by scheduler) |

### Example: POST /api/chat (PowerShell)

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method Post `
  -ContentType "application/json" `
  -Body '{"query": "What is the expense ratio of HDFC Small Cap Fund?"}'
```

**Response:**
```json
{
  "answer": "The expense ratio of HDFC Small Cap Fund Direct Growth is 0.68%.",
  "citation": {
    "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "scheme_name": "HDFC Small Cap Fund - Direct Growth",
    "fetch_date": "2026-08-07"
  },
  "last_updated": "2026-08-07",
  "query_type": "factual"
}
```

---

## Running Tests

```bash
# Using venv (Windows)
.\venv\Scripts\pytest tests/ -v

# Using venv (macOS/Linux)
./venv/bin/pytest tests/ -v
```

Expected output: **16 passed** — covers all 12 HDFC schemes for metadata pre-filtering, score threshold filtering, and chunk metadata validation.

### Running the Evaluation Script

```bash
.\venv\Scripts\python -m scripts.evaluate
```

Latest results against the gold-standard Q&A set:

| Metric | Score |
|--------|-------|
| Hit Rate (correct scheme retrieved) | **100%** |
| Answer Coverage (key terms present) | **100%** |
| Refusal Rate (advisory queries blocked) | **100%** |

---

## Automated Ingestion

The GitHub Actions workflow at [`.github/workflows/weekday-ingest.yml`](.github/workflows/weekday-ingest.yml) runs automatically every **Monday–Saturday at 10:30 AM IST** (05:00 UTC).

**Workflow steps:**
1. **Holiday check** — reads `data/holidays.json`, skips NSE/BSE holidays.
2. **Trigger ingestion** — calls `POST /api/admin/ingest` on the live Railway backend.
3. **Wait 45 seconds** — allows the background task to complete.
4. **Verify health** — checks `/api/health` for a non-zero chunk count.
5. **Failure alert** — creates a GitHub Issue with a link to the failed run log if any step fails.

You can also trigger it manually via the **Actions → Weekday Ingestion → Run workflow** button.

---

## Limitations

- **Facts only** — Never provides investment advice, comparisons, or predictions.
- **HDFC schemes only** — Only the 12 HDFC schemes listed above are in the corpus.
- **Groww dependency** — If Groww changes its HTML structure, the loader may need updating.
- **Data freshness** — Answers reflect the last ingested data (refreshed automatically each weekday).
- **No conversational memory** — Each query is stateless; no chat history is retained.
- **Free tier rate limits** — The Groq free tier limits RPM; the evaluation script uses automatic retry.

---

## Disclaimer

> This tool is for **informational purposes only** and does **not** constitute financial or investment advice. Past performance is not indicative of future results. Consult a SEBI-registered financial adviser before making investment decisions.  
> Data sourced from [Groww](https://groww.in) and [AMFI India](https://www.amfiindia.com).

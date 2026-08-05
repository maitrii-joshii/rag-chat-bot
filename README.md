# RAG Mutual Fund FAQ Assistant

> A facts-only Q&A chatbot for **HDFC Mutual Fund** schemes — powered by a RAG (Retrieval-Augmented Generation) pipeline using ChromaDB, BGE embeddings, and the Groq LLM API.

---

## Overview

This assistant answers **factual questions** about 12 HDFC Mutual Fund schemes (NAV, expense ratio, exit load, minimum SIP, fund category, etc.). It does **not** provide investment advice, performance comparisons, or predictions.

**Data source**: [Groww scheme pages](https://groww.in) — fetched, chunked, and embedded into a local ChromaDB vector store.

---

## Architecture

```
User Query
    │
    ▼
Guardrails (PII check → intent classification)
    │
    ├── Advisory / Comparison / Prediction → Polite Refusal
    └── Factual ──────────────────────────────────────────►
                                                    Retriever (BGE + ChromaDB)
                                                          │
                                                    Generator (Groq LLM)
                                                          │
                                                    Post-processor (validate)
                                                          │
                                                    Response (answer + citation)
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

| Layer | Technology |
|-------|-----------|
| Embedding | `BAAI/bge-small-en-v1.5` (sentence-transformers) |
| Vector Store | ChromaDB (persistent, local) |
| LLM | Groq API — `llama-3.1-8b-instant` |
| Framework | FastAPI + Uvicorn |
| Frontend | Vanilla HTML / CSS / JS |
| Scheduler | GitHub Actions (Mon–Sat, 10:30 AM IST) |
| Hosting | Railway (backend) + Vercel (frontend) |

---

## Project Structure

```
rag-chat-bot/
├── .github/workflows/      # GitHub Actions CI/CD
├── docs/                   # Architecture, implementation plan, context
├── src/
│   ├── main.py             # FastAPI application entry point
│   ├── ingestion/          # Loader → Preprocessor → Chunker → Embedder
│   ├── retrieval/          # Retriever + optional Reranker
│   ├── generation/         # Prompts + Generator (Groq) + Postprocessor
│   ├── guardrails/         # PII Detector + Intent Classifier + Refusal Handler
│   ├── api/                # FastAPI routes + Pydantic schemas
│   └── ui/                 # Static chat UI (HTML / CSS / JS)
├── data/
│   ├── corpus.yml          # HDFC scheme registry + Groww URLs
│   ├── holidays.json       # 2026 NSE/BSE + national holidays
│   └── vectorstore/        # ChromaDB (gitignored)
├── scripts/
│   ├── ingest.py           # Offline ingestion pipeline CLI
│   └── evaluate.py         # Batch evaluation script
├── tests/                  # pytest test suite
├── .env.example            # Environment variable template
├── requirements.txt        # Pinned Python dependencies
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com)

### 1. Clone & create virtual environment

```bash
git clone https://github.com/maitrii-joshii/rag-chat-bot.git
cd rag-chat-bot
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS / Linux)
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your-key-here
```

### 4. Run ingestion pipeline *(Phase 1)*

```bash
python scripts/ingest.py --config data/corpus.yml --output data/vectorstore
```

### 5. Start the API server *(Phase 4)*

```bash
uvicorn src.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Submit a factual query, receive an answer + citation |
| `GET` | `/api/health` | Service health check + vector store chunk count |
| `GET` | `/api/examples` | Return 3 example questions for the UI |

### Example: POST /api/chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the expense ratio of HDFC Small Cap Fund?"}'
```

```json
{
  "answer": "The expense ratio of HDFC Small Cap Fund Direct Growth is 0.68%. [Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth]",
  "citation": {
    "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "scheme_name": "HDFC Small Cap Fund - Direct Growth",
    "fetch_date": "2026-08-05"
  },
  "last_updated": "2026-08-05",
  "query_type": "factual"
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Automated Ingestion

The GitHub Actions workflow (`.github/workflows/weekday-ingest.yml`) runs the ingestion pipeline every **Monday to Saturday at 10:30 AM IST**, skipping NSE/BSE holidays listed in `data/holidays.json`. On failure, it automatically creates a GitHub Issue.

---

## Limitations

- **Facts only** — The assistant never provides investment advice, fund comparisons, or performance predictions.
- **HDFC schemes only** — Only the 12 HDFC schemes listed above are in the corpus.
- **Data freshness** — Answers reflect the most recently ingested Groww page data. Run `scripts/ingest.py` to refresh.
- **Groww dependency** — If Groww changes its HTML structure, the loader may need updating.
- **No conversational memory** — Each query is independent; no chat history is maintained.

---

## Disclaimer

> This tool is for **informational purposes only** and does **not** constitute financial or investment advice. Past performance is not indicative of future results. Consult a SEBI-registered financial adviser before making investment decisions.  
> Data sourced from [Groww](https://groww.in) and [AMFI India](https://www.amfiindia.com).

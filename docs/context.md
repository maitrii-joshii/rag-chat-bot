# Project Context — Mutual Fund FAQ Assistant

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | RAG Chat Bot — Mutual Fund FAQ Assistant |
| **Domain** | Personal Finance / Mutual Funds (India) |
| **Reference Product** | Groww (for product-context framing) |
| **Nature** | Facts-only Q&A — **zero** investment advice |

---

## 2. Problem Summary

Build a lightweight, **Retrieval-Augmented Generation (RAG)** assistant that answers **objective, verifiable** questions about mutual fund schemes. Every response must be backed by an official public source; the system must never offer opinions, recommendations, or performance comparisons.

### Why This Matters

- Retail investors need quick, trustworthy facts (expense ratios, exit loads, SIP minimums) without wading through lengthy documents.
- Support / content teams repeatedly answer the same factual queries — this assistant automates that.

---

## 3. Target Users

| Persona | Use-Case |
|---|---|
| **Retail Investors** | Comparing scheme details (expense ratio, lock-in, riskometer, benchmark) across 3–5 funds |
| **Customer Support / Content Teams** | Deflecting repetitive factual queries with accurate, source-cited answers |

---

## 4. Corpus & Data Pipeline

### 4.1 Corpus Composition

| # | Source Type | Examples |
|---|---|---|
| 1 | Scheme Factsheets | Monthly factsheet PDFs from the chosen AMC |
| 2 | KIM (Key Information Memorandum) | Fund-specific KIM documents |
| 3 | SID (Scheme Information Document) | Detailed scheme information documents |
| 4 | AMC FAQ / Help Pages | Official AMC website FAQ sections |
| 5 | AMFI / SEBI Guidance Pages | Regulatory guidance documents |
| 6 | Statement & Tax Guides | How-to guides for downloading statements, capital gains reports |

### 4.2 Corpus Rules

- **One AMC** must be selected as the primary data source.
- **3–5 schemes** covering diverse categories (e.g., Large-Cap, Flexi-Cap, ELSS).
- **15–25 official public URLs** to be curated — no third-party blogs or aggregator sites.
- All sources must be **official and publicly accessible** (AMC, AMFI, SEBI domains only).

### 4.3 Data Pipeline (High-Level)

```
[Official URLs / PDFs]
        │
        ▼
   ┌──────────┐
   │  Scraper / │
   │  Loader    │  ← Fetch & parse HTML / PDF content
   └────┬───────┘
        │
        ▼
   ┌──────────┐
   │  Chunker  │  ← Split documents into retrieval-friendly chunks
   └────┬───────┘
        │
        ▼
   ┌──────────────┐
   │  Embeddings   │  ← Generate vector embeddings for each chunk
   └────┬──────────┘
        │
        ▼
   ┌──────────────┐
   │  Vector Store │  ← Index embeddings for similarity search
   └──────────────┘
```

---

## 5. RAG Architecture Overview

```
┌─────────────┐        ┌────────────────┐        ┌─────────────┐
│  User Query  │──────▶│  Retriever      │──────▶│  LLM / Gen   │
└─────────────┘        │  (Vector Search)│        │  (Answer Gen)│
                       └────────────────┘        └──────┬──────┘
                                                        │
                                                        ▼
                                                 ┌─────────────┐
                                                 │  Response    │
                                                 │  (≤3 sentences│
                                                 │  + citation  │
                                                 │  + date)     │
                                                 └─────────────┘
```

### Key Components

| Component | Responsibility |
|---|---|
| **Document Loader** | Fetches and parses content from official URLs / PDFs |
| **Text Splitter / Chunker** | Breaks documents into semantically coherent chunks |
| **Embedding Model** | Converts text chunks into dense vector representations |
| **Vector Store** | Stores and indexes embeddings for fast similarity retrieval |
| **Retriever** | Given a query, retrieves the top-k most relevant chunks |
| **LLM (Generator)** | Synthesises a concise, factual answer from retrieved context |
| **Guardrails / Refusal Layer** | Detects advisory / out-of-scope queries and returns a polite refusal |

---

## 6. Supported Query Types

The assistant handles **facts-only** queries. Examples:

| Category | Sample Query |
|---|---|
| Expense Ratio | "What is the expense ratio of XYZ Fund — Direct Growth?" |
| Exit Load | "What is the exit load for ABC Flexi Cap Fund?" |
| Minimum SIP | "What is the minimum SIP amount for DEF ELSS Fund?" |
| Lock-in Period | "What is the lock-in period for ELSS funds?" |
| Riskometer | "What is the riskometer classification of XYZ Fund?" |
| Benchmark Index | "Which benchmark index does ABC Fund track?" |
| Process / How-To | "How do I download my capital gains statement?" |

---

## 7. Response Format Specification

Every valid response **must** conform to the following format:

| Element | Constraint |
|---|---|
| **Body** | Maximum **3 sentences**, factual and concise |
| **Citation** | Exactly **1 source link** (official URL) |
| **Footer** | `"Last updated from sources: <date>"` |

### Example Response

> The expense ratio of XYZ Flexi Cap Fund — Direct Growth is 0.39% (as of June 2026).
>
> Source: https://www.exampleamc.com/factsheet/xyz-flexi-cap
>
> *Last updated from sources: 2026-07-15*

---

## 8. Refusal Handling

### Triggers

Any query that is **advisory, comparative, or speculative** must be refused. Examples:

- "Should I invest in this fund?"
- "Which fund is better — X or Y?"
- "Will this fund give good returns?"
- Any performance comparison or return calculation request

### Refusal Response Rules

| Rule | Detail |
|---|---|
| **Tone** | Polite, clear, non-apologetic |
| **Explanation** | Reinforce the facts-only limitation |
| **Fallback Link** | Provide a relevant educational link (AMFI / SEBI resource) |

### Example Refusal

> I can only provide factual information about mutual fund schemes and cannot offer investment advice or comparisons. For guidance on investing, you may visit the AMFI investor awareness page: https://www.amfiindia.com/investor-corner/knowledge-center.html
>
> *Last updated from sources: 2026-07-15*

---

## 9. User Interface Requirements

The UI is intentionally **minimal**:

| Element | Description |
|---|---|
| **Welcome Message** | A brief greeting explaining the assistant's purpose |
| **Example Questions** | Display **3 clickable example questions** to guide first-time users |
| **Disclaimer Banner** | Persistently visible: `"Facts-only. No investment advice."` |
| **Chat Input** | Simple text input for user queries |
| **Response Area** | Displays the assistant's answer with citation and footer |

---

## 10. Hard Constraints

### 10.1 Data & Source Constraints

- ✅ Use **only** official public sources: AMC websites, AMFI, SEBI
- ❌ No third-party blogs, aggregators, or unofficial content
- ❌ No scraped user-generated content

### 10.2 Privacy & Security Constraints

The system must **never** collect, store, or process:

| Prohibited Data |
|---|
| PAN numbers |
| Aadhaar numbers |
| Bank account numbers |
| OTPs |
| Email addresses |
| Phone numbers |

### 10.3 Content Constraints

| Rule | Detail |
|---|---|
| No investment advice | No recommendations, "buy/sell" signals, or suitability opinions |
| No performance comparisons | No return calculations or fund-vs-fund rankings |
| Performance queries → factsheet link | For any performance-related question, respond with the official factsheet URL only |

### 10.4 Transparency Constraints

- Every answer must be **short, factual, and verifiable**
- Every answer must include a **source link** and **last-updated date**

---

## 11. Expected Deliverables

| Deliverable | Details |
|---|---|
| **README.md** | Setup instructions, selected AMC & schemes, architecture overview, known limitations |
| **Disclaimer Snippet** | `"Facts-only. No investment advice."` — embedded in UI and README |
| **Working Assistant** | Functional RAG pipeline with chat interface |
| **Curated Corpus** | 15–25 official URLs, documented |

---

## 12. Success Criteria

| # | Criterion | Measurement |
|---|---|---|
| 1 | **Accurate retrieval** | Correct factual information returned for supported query types |
| 2 | **Facts-only adherence** | Zero advisory or opinionated responses in testing |
| 3 | **Consistent citations** | Every response includes a valid, relevant source link |
| 4 | **Proper refusal** | Advisory queries are politely declined with an educational fallback link |
| 5 | **Clean UI** | Minimal, user-friendly interface with disclaimer, examples, and chat |

---

## 13. Key Design Principles

1. **Accuracy over intelligence** — The system prioritizes verified facts over creative generation.
2. **Transparency** — Every claim is traceable to a public source.
3. **Compliance** — No financial advice; aligned with SEBI/AMFI communication guidelines.
4. **Simplicity** — Minimal UI, concise responses, no feature bloat.
5. **Privacy-first** — No PII collection or storage, ever.

---

## 14. Glossary

| Term | Definition |
|---|---|
| **AMC** | Asset Management Company — the entity managing mutual fund schemes |
| **AMFI** | Association of Mutual Funds in India — industry body |
| **SEBI** | Securities and Exchange Board of India — the regulatory authority |
| **KIM** | Key Information Memorandum — a summary document for a mutual fund scheme |
| **SID** | Scheme Information Document — detailed legal document describing a scheme |
| **ELSS** | Equity Linked Savings Scheme — a tax-saving mutual fund category |
| **SIP** | Systematic Investment Plan — periodic investment into a mutual fund |
| **RAG** | Retrieval-Augmented Generation — an architecture combining information retrieval with LLM generation |
| **NAV** | Net Asset Value — the per-unit price of a mutual fund |
| **Exit Load** | A fee charged when units are redeemed before a specified period |
| **Riskometer** | A standardised risk classification label (Low to Very High) mandated by SEBI |

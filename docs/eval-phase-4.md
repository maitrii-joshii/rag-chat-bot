# Evaluation Criteria — Phase 4: API & Frontend

> **Phase**: 4 — API & Frontend  
> **Duration**: ~1.5 days  
> **Derived From**: [implementationPlan.md](./implementationPlan.md) · [architecture.md §9](./architecture.md#9-api--interface-layer)

---

## Overview

Phase 4 exposes the RAG engine via FastAPI endpoints and builds the minimal chat UI. Evaluation focuses on **API correctness, request validation, UI functionality, and responsiveness**.

---

## Evaluation Categories

### 1. API — `/api/chat` Endpoint

**Criteria**: The chat endpoint handles all query types correctly with proper JSON responses.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.1.1 | Factual query returns correct JSON | `POST /api/chat {"query": "What is the expense ratio of HDFC Small Cap Fund?"}` | HTTP 200, response has `answer`, `citation`, `last_updated`, `query_type: "factual"` |
| E-4.1.2 | Advisory query returns refusal JSON | `POST /api/chat {"query": "Should I invest in HDFC Small Cap?"}` | HTTP 200, `query_type: "refused"`, polite refusal text |
| E-4.1.3 | PII query returns block response | `POST /api/chat {"query": "My PAN is ABCDE1234F"}` | HTTP 200, `query_type: "blocked"`, PII warning |
| E-4.1.4 | Empty query returns validation error | `POST /api/chat {"query": ""}` | HTTP 400, clear error message |
| E-4.1.5 | Missing query field returns error | `POST /api/chat {}` | HTTP 422, Pydantic validation error |
| E-4.1.6 | Long query is handled | `POST /api/chat {"query": "a" * 2000}` | HTTP 400 (exceeds max length) OR truncated + processed |
| E-4.1.7 | Whitespace-only query returns error | `POST /api/chat {"query": "   "}` | HTTP 400, "Query cannot be empty" |
| E-4.1.8 | Non-JSON body returns error | `POST /api/chat` with plain text body | HTTP 422, "Invalid JSON" |
| E-4.1.9 | Citation URL in response is valid | Validate URL format in 5 responses | All URLs match `https://groww.in/mutual-funds/...` |
| E-4.1.10 | Response time < 3s | Time 10 requests | Average < 3s, P95 < 5s |

### 2. API — `/api/health` Endpoint

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.2.1 | Returns healthy status | `GET /api/health` | HTTP 200, `{"status": "healthy", "vectorstore_chunks": N}` where N > 0 |
| E-4.2.2 | Reports chunk count | Check `vectorstore_chunks` field | Count matches actual ChromaDB collection count |
| E-4.2.3 | Reports unhealthy if vector store is missing | Remove vector store temporarily | Returns `{"status": "unhealthy", ...}` or HTTP 503 |

### 3. API — `/api/examples` Endpoint

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.3.1 | Returns 3 example questions | `GET /api/examples` | HTTP 200, `{"examples": [...]}` with exactly 3 items |
| E-4.3.2 | Examples are valid queries | Submit each example to `/api/chat` | All 3 return factual responses (not refused) |
| E-4.3.3 | Examples mention HDFC schemes | Check example text | Each references an HDFC fund |

### 4. API — Middleware & Security

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.4.1 | CORS allows configured origins | Request from Vercel domain | `Access-Control-Allow-Origin` header present |
| E-4.4.2 | CORS blocks disallowed origins | Request from `http://evil.com` | CORS error / missing header |
| E-4.4.3 | Rate limiting triggers after threshold | Send 35 requests in 1 minute from same IP | HTTP 429 after ~30 requests |
| E-4.4.4 | XSS in query does not reflect in response | Send `<script>alert('xss')</script>` as query | No script tags in response body |
| E-4.4.5 | Server does not expose stack traces | Trigger an internal error | HTTP 500 with generic message, no traceback |

### 5. Frontend — UI Layout & Components

**Criteria**: All UI elements from [architecture.md §9.2](./architecture.md#92-ui-components) are present and functional.

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.5.1 | Disclaimer banner visible | Open `http://localhost:8000` | "Facts-only. No investment advice." banner at top |
| E-4.5.2 | Disclaimer always visible | Scroll down in chat | Banner stays fixed / always visible |
| E-4.5.3 | Welcome message displayed | Initial page load | Greeting + assistant description visible |
| E-4.5.4 | 3 example questions displayed | Initial page load | 3 clickable example question buttons/cards |
| E-4.5.5 | Chat input field present | Visual check | Text input + Send button visible |
| E-4.5.6 | Response area present | Visual check | Chat history area visible (empty initially) |

### 6. Frontend — Interaction & Functionality

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.6.1 | Clicking example question sends query | Click any example | Query appears in chat, response loads |
| E-4.6.2 | Typing + Send button submits query | Type query, click Send | Query sent, response displayed |
| E-4.6.3 | Pressing Enter submits query | Type query, press Enter | Same as clicking Send |
| E-4.6.4 | Loading indicator during request | Submit query, observe | Spinner or "Thinking..." shown during API call |
| E-4.6.5 | Send button disabled while loading | Submit query, try clicking Send again | Button disabled until response arrives |
| E-4.6.6 | Empty input doesn't submit | Click Send with empty input | Nothing happens, no API call |
| E-4.6.7 | Response displays answer text | Submit factual query | Answer text visible in chat |
| E-4.6.8 | Response displays citation link | Submit factual query | Clickable Groww URL visible |
| E-4.6.9 | Response displays "Last updated" footer | Submit factual query | Footer visible below answer |
| E-4.6.10 | Refusal response displays correctly | Submit advisory query | Polite refusal + AMFI link visible |
| E-4.6.11 | Chat history preserves messages | Submit 3 queries | All 3 Q&A pairs visible in history |
| E-4.6.12 | Auto-scroll to latest message | Submit multiple queries | Chat scrolls to newest message |
| E-4.6.13 | Error state handled | Disconnect backend, submit query | User-friendly error message (not raw error) |

### 7. Frontend — Responsiveness & Compatibility

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.7.1 | Desktop layout (1920×1080) | Browser at full width | All elements properly laid out |
| E-4.7.2 | Tablet layout (768×1024) | Resize browser | Layout adapts, no overflow |
| E-4.7.3 | Mobile layout (375×812) | Resize browser or use DevTools | All elements visible, input usable |
| E-4.7.4 | Chrome compatibility | Open in Chrome | All features work |
| E-4.7.5 | Firefox compatibility | Open in Firefox | All features work |
| E-4.7.6 | No JavaScript errors in console | Open DevTools console | Zero errors on page load and interaction |
| E-4.7.7 | `<noscript>` fallback | Disable JavaScript | Shows "JavaScript is required" message |

### 8. Frontend — Security

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-4.8.1 | No XSS via user input | Submit `<img src=x onerror=alert(1)>` as query | Input rendered as text, not as HTML |
| E-4.8.2 | No XSS via API response | Mock API response with HTML | Response rendered as text, not executed |
| E-4.8.3 | External links open in new tab | Click citation URL | Opens in `target="_blank"` with `rel="noopener"` |

---

## Integration Test Checklist

Full end-to-end flow through API + UI:

| # | Scenario | Steps | Pass Condition |
|---|----------|-------|----------------|
| INT-1 | Happy path — factual query | Type "What is the expense ratio of HDFC Small Cap Fund?" → Send | Answer + citation + footer displayed in chat |
| INT-2 | Advisory refusal | Type "Should I invest in HDFC Defence Fund?" → Send | Polite refusal + AMFI link displayed |
| INT-3 | PII block | Type "My PAN is ABCDE1234F" → Send | Warning message displayed |
| INT-4 | Example question click | Click first example question | Query sent, response displayed |
| INT-5 | Multiple queries in session | Submit 5 different queries | All 5 Q&A pairs in chat history |
| INT-6 | Error handling | Stop backend, submit query | "Unable to connect" message |

---

## Scoring Rubric

| Rating | Criteria |
|--------|----------|
| ✅ **Pass** | All 3 API endpoints working; all UI components present; all interaction tests pass; responsive on mobile |
| ⚠️ **Conditional Pass** | API working; UI functional but ≤ 2 minor visual issues; mobile has minor layout issues |
| ❌ **Fail** | Any API endpoint returns incorrect data; XSS vulnerability; UI missing critical components (disclaimer, input, response area) |

---

> **Previous**: [eval-phase-3.md](./eval-phase-3.md) — Guardrails & Safety  
> **Next**: [eval-phase-5.md](./eval-phase-5.md) — Deployment & Automation

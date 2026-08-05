# Evaluation Criteria — Phase 5: Deployment, Automation & Polish

> **Phase**: 5 — Deploy & Automate  
> **Duration**: ~1 day  
> **Derived From**: [implementationPlan.md](./implementationPlan.md) · [architecture.md §5, §15](./architecture.md#5-scheduler--automated-ingestion-github-actions)

---

## Overview

Phase 5 deploys the system to production (Vercel + Railway), sets up the GitHub Actions ingestion scheduler, writes tests, and finalises documentation. Evaluation covers **deployment health, scheduler correctness, test coverage, and documentation completeness**.

---

## Evaluation Categories

### 1. Railway Backend Deployment

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.1.1 | Backend is live and reachable | `curl https://<app>.up.railway.app/api/health` | HTTP 200, `{"status": "healthy"}` |
| E-5.1.2 | Groq API key is configured | Submit a chat query | Response generated (not an API key error) |
| E-5.1.3 | ChromaDB persistent volume works | Restart Railway service, query again | Vector store data survives restart |
| E-5.1.4 | Environment variables set correctly | Check Railway dashboard | `GROQ_API_KEY`, `EMBEDDING_MODEL`, `VECTORSTORE_PATH` all configured |
| E-5.1.5 | Start command is correct | Check Railway logs | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` starts successfully |
| E-5.1.6 | Cold start time is acceptable | First request after idle period | Response within 15s (cold start) |
| E-5.1.7 | Warm request latency | Subsequent requests | < 3s average latency |

### 2. Vercel Frontend Deployment

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.2.1 | Frontend is live and reachable | Open `https://<app>.vercel.app` in browser | Page loads with all UI components |
| E-5.2.2 | `BACKEND_URL` correctly configured | Submit a query from Vercel frontend | Query reaches Railway backend, response displayed |
| E-5.2.3 | Static assets load correctly | Check Network tab in DevTools | `index.html`, `style.css`, `script.js` all HTTP 200 |
| E-5.2.4 | No mixed content warnings | Check browser console | No HTTP/HTTPS mixed content errors |
| E-5.2.5 | Auto-deploy from GitHub works | Push a commit → check Vercel | New deployment triggered and live within 2 min |

### 3. CORS Configuration

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.3.1 | Vercel origin allowed by Railway CORS | Browser request from Vercel → Railway | No CORS errors in browser console |
| E-5.3.2 | Preflight OPTIONS request works | `curl -X OPTIONS <railway-url>/api/chat` with Vercel origin | HTTP 200 with correct CORS headers |
| E-5.3.3 | Disallowed origin blocked | Request from `http://localhost:9999` | CORS error (expected) |

### 4. End-to-End Production Smoke Test

| # | Scenario | Steps | Pass Condition |
|---|----------|-------|----------------|
| E-5.4.1 | Factual query via Vercel UI | Open Vercel URL → ask "What is the expense ratio of HDFC Small Cap Fund?" | Correct answer + Groww citation displayed |
| E-5.4.2 | Advisory refusal via Vercel UI | Ask "Should I invest in HDFC Defence Fund?" | Polite refusal + AMFI link displayed |
| E-5.4.3 | PII block via Vercel UI | Submit "My PAN is ABCDE1234F" | PII warning displayed |
| E-5.4.4 | Example question click | Click any example question | Response displayed correctly |
| E-5.4.5 | Health check | `curl <railway-url>/api/health` | `{"status": "healthy", "vectorstore_chunks": N}` where N > 0 |
| E-5.4.6 | Mobile access | Open Vercel URL on mobile device or emulator | UI is responsive and usable |

---

### 5. GitHub Actions — Weekday Ingestion Scheduler

#### 5A. Workflow Configuration

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.5.1 | Workflow file exists | `cat .github/workflows/weekday-ingest.yml` | File exists and is valid YAML |
| E-5.5.2 | Cron expression is correct | Check `cron:` line | `0 5 * * 1-6` (Mon–Sat, 05:00 UTC = 10:30 AM IST) |
| E-5.5.3 | Manual dispatch enabled | Check `workflow_dispatch:` | Present with `full_reindex` and `skip_holiday_check` inputs |
| E-5.5.4 | Python version specified | Check `python-version` | `3.11` |
| E-5.5.5 | Timeout set | Check `timeout-minutes` | `30` |

#### 5B. Holiday Check Job

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.5.6 | Holiday detected — ingestion skipped | Set today's date in `holidays.json`, trigger workflow | `check-holiday` outputs `is_holiday=true`, `ingest` job skipped |
| E-5.5.7 | Non-holiday — ingestion proceeds | Ensure today is NOT in `holidays.json`, trigger workflow | `check-holiday` outputs `is_holiday=false`, `ingest` job runs |
| E-5.5.8 | Missing `holidays.json` — default to business day | Remove `holidays.json` temporarily | Warning logged, ingestion proceeds |
| E-5.5.9 | `skip_holiday_check` override | Manual dispatch with `skip_holiday_check=true` on a holiday | Ingestion runs despite holiday |

#### 5C. Ingestion Job

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.5.10 | Ingestion script runs in CI | Trigger manual dispatch | `python scripts/ingest.py` exits with code 0 |
| E-5.5.11 | Vector store committed on change | Check git log after ingestion | New commit with `chore: weekday corpus ingestion <date>` |
| E-5.5.12 | No commit when nothing changed | Trigger twice in succession | Second run: "No changes — skipping commit" |
| E-5.5.13 | `--force` flag works | Manual dispatch with `full_reindex=true` | Full re-ingestion occurs |

#### 5D. Failure Handling

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.5.14 | GitHub Issue created on failure | Force ingestion failure (bad URL) | Issue created with title `🔴 Weekday Ingestion Failed — <date>` |
| E-5.5.15 | Issue has correct labels | Check created issue | Labels: `bug`, `ingestion` |
| E-5.5.16 | Issue body has workflow run link | Check issue body | Contains link to failed GitHub Actions run |

---

### 6. Test Suite

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.6.1 | All guardrail tests pass | `pytest tests/test_guardrails.py -v` | 100% pass rate |
| E-5.6.2 | All refusal tests pass | `pytest tests/test_refusal.py -v` | 100% pass rate |
| E-5.6.3 | All retriever tests pass | `pytest tests/test_retriever.py -v` | 100% pass rate |
| E-5.6.4 | Test coverage for guardrails | Review test file | ≥ 20 test cases (PII + advisory + refusal) |
| E-5.6.5 | Test coverage for retriever | Review test file | ≥ 2 queries per scheme (24 total) |
| E-5.6.6 | Evaluation script runs | `python scripts/evaluate.py` | Produces pass/fail report |

### 7. Documentation

| # | Check | Method | Pass Condition |
|---|-------|--------|----------------|
| E-5.7.1 | `README.md` exists and is non-trivial | `wc -l README.md` | ≥ 50 lines |
| E-5.7.2 | README has setup instructions | Manual review | Step-by-step local setup guide |
| E-5.7.3 | README lists AMC and all 12 schemes | Manual review | HDFC Mutual Fund + 12 scheme names |
| E-5.7.4 | README has architecture overview | Manual review | High-level diagram or description |
| E-5.7.5 | README has known limitations | Manual review | At least 3 documented limitations |
| E-5.7.6 | README has disclaimer | Manual review | "Facts-only. No investment advice." present |
| E-5.7.7 | Deployment URLs documented | Manual review | Vercel + Railway URLs (or placeholders) |

---

## Final Production Readiness Checklist

| # | Category | Check | Status |
|---|----------|-------|--------|
| 1 | **Data** | All 12 schemes ingested and searchable | ☐ |
| 2 | **RAG** | Factual queries return correct, cited answers | ☐ |
| 3 | **Safety** | PII blocked, advisory refused, out-of-scope handled | ☐ |
| 4 | **API** | All 3 endpoints responding correctly | ☐ |
| 5 | **UI** | Disclaimer, examples, chat, responsive layout | ☐ |
| 6 | **Deployment** | Vercel (frontend) + Railway (backend) live | ☐ |
| 7 | **CORS** | Cross-origin requests working | ☐ |
| 8 | **Scheduler** | GitHub Actions cron configured and tested | ☐ |
| 9 | **Tests** | All test suites pass | ☐ |
| 10 | **Docs** | README complete with setup + limitations | ☐ |

---

## Scoring Rubric

| Rating | Criteria |
|--------|----------|
| ✅ **Pass** | All production readiness checks pass; scheduler tested; full test suite green; README complete |
| ⚠️ **Conditional Pass** | 8/10 readiness checks pass; minor scheduler issues; README has minor gaps |
| ❌ **Fail** | Deployment down; CORS broken; scheduler not functional; < 70% tests pass |

---

> **Previous**: [eval-phase-4.md](./eval-phase-4.md) — API & Frontend  
> **All Phases Complete** 🎉

---

## Cross-Phase Evaluation Summary

| Phase | Eval File | Key Metrics |
|-------|-----------|-------------|
| 0 | [eval-phase-0.md](./eval-phase-0.md) | Directory structure, deps, config validity |
| 1 | [eval-phase-1.md](./eval-phase-1.md) | 12/12 URLs fetched, chunking quality, vector store populated |
| 2 | [eval-phase-2.md](./eval-phase-2.md) | 12/12 scheme retrieval, response format, < 3s latency |
| 3 | [eval-phase-3.md](./eval-phase-3.md) | PII recall = 100%, advisory recall ≥ 95%, zero PII leakage |
| 4 | [eval-phase-4.md](./eval-phase-4.md) | API correctness, UI completeness, mobile responsive |
| 5 | [eval-phase-5.md](./eval-phase-5.md) | Production live, scheduler tested, tests green, docs complete |

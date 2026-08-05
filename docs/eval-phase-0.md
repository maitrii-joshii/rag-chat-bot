# Evaluation Criteria — Phase 0: Project Scaffold & Configuration

> **Phase**: 0 — Scaffold & Config  
> **Duration**: ~0.5 day  
> **Derived From**: [implementationPlan.md](./implementationPlan.md) · [architecture.md](./architecture.md)

---

## Overview

Phase 0 establishes the project foundation — directory structure, dependencies, configuration files, and version control. Evaluation focuses on **correctness, completeness, and reproducibility** of the scaffold.

---

## Evaluation Categories

### 1. Directory Structure Completeness

**Criteria**: Every directory and placeholder file defined in [architecture.md §12](./architecture.md#12-directory-structure) must exist.

| # | Check | Command / Method | Pass Condition |
|---|-------|-----------------|----------------|
| E-0.1.1 | All source directories exist | `ls src/ingestion src/retrieval src/generation src/guardrails src/api src/ui` | All directories exist, no errors |
| E-0.1.2 | All `__init__.py` files exist | `find src -name "__init__.py"` | Found in `src/`, `src/ingestion/`, `src/retrieval/`, `src/generation/`, `src/guardrails/`, `src/api/` |
| E-0.1.3 | Data directories exist | `ls data/ data/vectorstore/` | Both directories exist |
| E-0.1.4 | Scripts directory exists | `ls scripts/ingest.py scripts/evaluate.py` | Both files exist |
| E-0.1.5 | Tests directory exists | `ls tests/` | Directory exists with at least placeholder test files |
| E-0.1.6 | GitHub Actions directory exists | `ls .github/workflows/` | Directory exists |
| E-0.1.7 | Docs directory is intact | `ls docs/` | All existing docs preserved, no accidental deletions |

### 2. Dependency Management

**Criteria**: All dependencies install cleanly and are pinned to stable versions.

| # | Check | Command / Method | Pass Condition |
|---|-------|-----------------|----------------|
| E-0.2.1 | `requirements.txt` exists and is non-empty | `cat requirements.txt` | File exists with ≥ 10 dependencies listed |
| E-0.2.2 | All dependencies install without errors | `pip install -r requirements.txt` | Exit code 0, no build failures |
| E-0.2.3 | Core dependencies present | `grep -E "fastapi\|uvicorn\|chromadb\|sentence-transformers\|groq\|langchain\|beautifulsoup4" requirements.txt` | All 7 core packages listed |
| E-0.2.4 | No conflicting versions | `pip check` | "No broken requirements found" |
| E-0.2.5 | Python version compatibility | `python --version` | Python 3.11+ |

### 3. Configuration Files

**Criteria**: All config files are valid, complete, and match the architecture spec.

| # | Check | Command / Method | Pass Condition |
|---|-------|-----------------|----------------|
| E-0.3.1 | `.env.example` exists with all variables | Manual review | Contains: `LLM_PROVIDER`, `LLM_MODEL`, `GROQ_API_KEY`, `EMBEDDING_MODEL`, `VECTORSTORE_PATH`, `VECTORSTORE_COLLECTION`, `RETRIEVAL_TOP_K`, `RETRIEVAL_SCORE_THRESHOLD`, `APP_HOST`, `APP_PORT` |
| E-0.3.2 | `.env.example` has NO real secrets | `grep -v "your-\|placeholder\|xxx" .env.example` | No actual API keys or passwords |
| E-0.3.3 | `data/corpus.yml` is valid YAML | `python -c "import yaml; yaml.safe_load(open('data/corpus.yml'))"` | No parsing errors |
| E-0.3.4 | `data/corpus.yml` contains 12 HDFC schemes | `grep -c "scheme:" data/corpus.yml` | Count = 12 |
| E-0.3.5 | `data/corpus.yml` has all 12 Groww URLs | `grep -c "groww.in" data/corpus.yml` | Count = 12 |
| E-0.3.6 | `data/holidays.json` is valid JSON | `python -c "import json; json.load(open('data/holidays.json'))"` | No parsing errors |
| E-0.3.7 | `data/holidays.json` contains 2026 holidays | `python -c "import json; h=json.load(open('data/holidays.json')); assert all(d.startswith('2026') for d in h)"` | All dates are 2026 |
| E-0.3.8 | `data/holidays.json` has ≥ 15 entries | `python -c "import json; assert len(json.load(open('data/holidays.json'))) >= 15"` | At least 15 holidays |

### 4. Version Control

**Criteria**: Git is initialised with proper ignore rules.

| # | Check | Command / Method | Pass Condition |
|---|-------|-----------------|----------------|
| E-0.4.1 | `.gitignore` exists | `cat .gitignore` | File exists and is non-empty |
| E-0.4.2 | `.env` is ignored | `grep ".env" .gitignore` | `.env` pattern present |
| E-0.4.3 | `__pycache__` is ignored | `grep "__pycache__" .gitignore` | Pattern present |
| E-0.4.4 | `data/vectorstore/` is ignored | `grep "vectorstore" .gitignore` | Pattern present |
| E-0.4.5 | `venv/` is ignored | `grep "venv" .gitignore` | Pattern present |
| E-0.4.6 | Initial commit complete | `git log --oneline -1` | At least one commit exists |

---

## Scoring Rubric

| Rating | Criteria |
|--------|----------|
| ✅ **Pass** | All checks in all 4 categories pass |
| ⚠️ **Conditional Pass** | ≤ 2 non-critical checks fail (E-0.1.5, E-0.1.6, E-0.4.6 are non-critical) |
| ❌ **Fail** | Any critical check fails (E-0.2.2, E-0.3.3, E-0.3.4, E-0.3.5) |

---

## Quick Validation Script

```bash
#!/bin/bash
echo "=== Phase 0 Evaluation ==="

echo "--- Directory Structure ---"
for dir in src/ingestion src/retrieval src/generation src/guardrails src/api src/ui data scripts tests .github/workflows; do
  [ -d "$dir" ] && echo "✅ $dir" || echo "❌ $dir MISSING"
done

echo "--- Config Files ---"
for f in .env.example data/corpus.yml data/holidays.json .gitignore requirements.txt; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ $f MISSING"
done

echo "--- Dependencies ---"
pip install -r requirements.txt --dry-run 2>&1 | tail -1

echo "--- YAML/JSON Validation ---"
python -c "import yaml; yaml.safe_load(open('data/corpus.yml')); print('✅ corpus.yml valid')" 2>&1 || echo "❌ corpus.yml invalid"
python -c "import json; json.load(open('data/holidays.json')); print('✅ holidays.json valid')" 2>&1 || echo "❌ holidays.json invalid"

echo "--- Corpus Count ---"
python -c "
import yaml
with open('data/corpus.yml') as f:
    data = yaml.safe_load(f)
schemes = len(data.get('schemes', []))
sources = len(data.get('sources', []))
print(f'Schemes: {schemes}/12, Sources: {sources}/12')
assert schemes == 12 and sources == 12, 'FAIL: Expected 12 schemes and 12 sources'
print('✅ Corpus count correct')
"

echo "=== Phase 0 Evaluation Complete ==="
```

---

> **Next**: [eval-phase-1.md](./eval-phase-1.md) — Data Ingestion Pipeline

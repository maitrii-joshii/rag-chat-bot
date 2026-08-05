"""Smoke tests for generation layer (Tasks 2.4-2.8) -- no Groq API key needed."""
import sys
sys.path.insert(0, ".")

from src.ingestion.loader import Document
from src.generation.prompts import build_context_prompt, format_citation, SYSTEM_PROMPT
from src.generation.postprocessor import (
    validate_response,
    extract_citation_url,
    extract_last_updated,
    _split_sentences,
)
from src.generation.generator import generate, NO_INFORMATION_RESPONSE

# ── Helpers ───────────────────────────────────────────────────────────────────
def make_chunk(text, scheme="HDFC Small Cap Fund - Direct Growth",
               url="https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
               date="2026-08-05", score=0.91):
    return Document(text=text, metadata={
        "scheme_name": scheme, "source_url": url,
        "fetch_date": date, "chunk_index": 0,
        "chunk_text": text, "similarity_score": score,
    })

# ── Task 2.4: System prompt sanity ────────────────────────────────────────────
print("Testing SYSTEM_PROMPT (Task 2.4)...")
assert "facts-only" in SYSTEM_PROMPT.lower()
assert "Last updated from sources:" in SYSTEM_PROMPT
assert "[Source:" in SYSTEM_PROMPT
assert "NEVER" in SYSTEM_PROMPT
print("  PASS: system prompt contains required keywords")

# ── Task 2.5: build_context_prompt ────────────────────────────────────────────
print("\nTesting build_context_prompt (Task 2.5)...")
chunks = [
    make_chunk("The expense ratio is 0.68% per annum.", score=0.92),
    make_chunk("Exit load is 1% if redeemed within 1 year.", score=0.85),
]
prompt = build_context_prompt("What is the expense ratio?", chunks)
assert "[Chunk 1]" in prompt
assert "[Chunk 2]" in prompt
assert "0.68%" in prompt
assert "groww.in" in prompt
assert "2026-08-05" in prompt
assert "What is the expense ratio?" in prompt
print("  PASS: prompt contains both chunks with metadata")

# Empty chunks
empty_prompt = build_context_prompt("test", [])
assert "No relevant context" in empty_prompt
print("  PASS: empty chunks returns no-context prompt")

# format_citation
citation = format_citation(chunks[0])
assert citation["url"] == "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth"
assert citation["scheme_name"] == "HDFC Small Cap Fund - Direct Growth"
assert citation["fetch_date"] == "2026-08-05"
print("  PASS: format_citation extracts metadata correctly")

# ── Task 2.7: validate_response ───────────────────────────────────────────────
print("\nTesting validate_response (Task 2.7)...")

# Valid response
valid = (
    "The expense ratio of HDFC Small Cap Fund Direct Growth is 0.68% per annum. "
    "[Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth] "
    "Last updated from sources: 2026-08-05"
)
result = validate_response(valid)
assert "0.68%" in result
print("  PASS: valid response accepted")

# Missing citation raises ValueError
no_citation = "The expense ratio is 0.68%. Last updated from sources: 2026-08-05"
try:
    validate_response(no_citation)
    print("  FAIL: should have raised ValueError")
except ValueError as e:
    print(f"  PASS: missing citation raises ValueError")

# Missing footer raises ValueError
no_footer = "The expense ratio is 0.68%. [Source: https://groww.in/test]"
try:
    validate_response(no_footer)
    print("  FAIL: should have raised ValueError")
except ValueError:
    print("  PASS: missing footer raises ValueError")

# Empty response
try:
    validate_response("")
    print("  FAIL: should have raised ValueError")
except ValueError:
    print("  PASS: empty response raises ValueError")

# Sentence limit: 5 sentences -> truncated to 3
long_response = (
    "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. "
    "[Source: https://groww.in/test] "
    "Last updated from sources: 2026-08-05"
)
truncated = validate_response(long_response)
body_part = truncated.split("[Source:")[0].strip()
sentence_count = len([s for s in body_part.split(". ") if s.strip()])
assert sentence_count <= 3, f"Expected <= 3 sentences, got {sentence_count}: {body_part!r}"
print(f"  PASS: long response truncated to {sentence_count} sentences")

# No-information response passes without citation/footer
no_info = "I don't have that information in my current knowledge base. Please visit https://www.amfiindia.com for authoritative fund details. Last updated from sources: N/A"
result = validate_response(no_info)
assert result == no_info
print("  PASS: no-information response passes validation")

# extract_citation_url
url = extract_citation_url(valid)
assert url == "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth", f"Got: {url!r}"
print("  PASS: extract_citation_url works")

# extract_last_updated
date = extract_last_updated(valid)
assert date == "2026-08-05", f"Got: {date!r}"
print("  PASS: extract_last_updated works")

# ── Task 2.8: No-information fallback ─────────────────────────────────────────
print("\nTesting no-information fallback (Task 2.8)...")
# Empty chunks -> fallback immediately (no Groq API call)
result = generate("What is the expense ratio?", chunks=[])
assert result == NO_INFORMATION_RESPONSE
assert "amfiindia.com" in result
assert "Last updated from sources: N/A" in result
print(f"  PASS: empty chunks returns NO_INFORMATION_RESPONSE")

# GROQ_API_KEY not set -> EnvironmentError when chunks provided
try:
    import os
    os.environ.pop("GROQ_API_KEY", None)
    # Reset cached client so the error triggers fresh
    from src.generation import generator as _gen_mod
    _gen_mod._groq_client_cache.clear()
    generate("test", chunks=[make_chunk("some text")])
    print("  FAIL: should have raised EnvironmentError")
except EnvironmentError as e:
    print(f"  PASS: missing GROQ_API_KEY raises EnvironmentError")

print()
print("All smoke tests passed.")

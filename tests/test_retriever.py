"""
tests/test_retriever.py — Unit Tests for Retrieval Module (Phase 5)

Tests:
  - retrieve() returns relevant chunks for factual queries on each HDFC scheme
  - Score threshold (>= 0.65) correctly filters irrelevant chunks
  - Metadata pre-filtering by scheme_name works
  - Empty list returned when no chunks meet the threshold
  - Covers all 12 HDFC schemes
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from src.retrieval.retriever import retrieve, preprocess_query, detect_scheme
from src.ingestion.loader import Document


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_chroma():
    """Mock the ChromaDB client and collection."""
    with patch("src.retrieval.retriever.chromadb.PersistentClient") as mock_client:
        mock_instance = MagicMock()
        mock_collection = MagicMock()
        
        # Default mock response for collection.query()
        mock_collection.query.return_value = {
            "documents": [["Chunk 1 text", "Chunk 2 text"]],
            "metadatas": [[
                {"source_url": "http://x", "scheme_name": "Mock Scheme", "fetch_date": "2026-08-01"},
                {"source_url": "http://y", "scheme_name": "Mock Scheme", "fetch_date": "2026-08-01"}
            ]],
            # Distances: 0.1 -> similarity 0.95 (keep), 0.8 -> similarity 0.60 (filter out if threshold=0.65)
            "distances": [[0.1, 0.8]]
        }
        mock_collection.count.return_value = 100
        mock_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_instance
        
        yield mock_collection


@pytest.fixture
def mock_embedder():
    """Mock the sentence-transformers model."""
    with patch("src.retrieval.retriever._get_or_load_model") as mock_get_model:
        mock_model = MagicMock()
        # Return a dummy embedding vector
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)
        mock_get_model.return_value = mock_model
        yield mock_model


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRetriever:
    """Tests for src.retrieval.retriever"""

    def test_retrieve_returns_list(self, mock_chroma, mock_embedder):
        """retrieve() should always return a list (never raise on valid input)."""
        results = retrieve("What is the NAV?")
        assert isinstance(results, list)
        assert len(results) == 1  # Second chunk filtered due to 0.60 score < 0.65 threshold
        assert isinstance(results[0], Document)
        assert results[0].text == "Chunk 1 text"

    def test_retrieve_empty_when_no_match(self, mock_chroma, mock_embedder):
        """An off-topic query should return an empty list (score threshold filters all)."""
        # Mock Chroma returning only high-distance (low similarity) chunks
        mock_chroma.query.return_value = {
            "documents": [["Irrelevant 1", "Irrelevant 2"]],
            "metadatas": [[{}, {}]],
            "distances": [[1.0, 1.2]] # Similarities: 0.5, 0.4 (both < 0.65)
        }
        results = retrieve("What is the weather today?")
        assert results == []

    @pytest.mark.parametrize("query,expected_canonical", [
        ("What is the expense ratio of HDFC Small Cap Fund?", "HDFC Small Cap Fund - Direct Growth"),
        ("What is the exit load for HDFC Large Cap Fund?", "HDFC Large Cap Fund - Direct Growth"),
        ("What is the minimum SIP amount for HDFC Mid Cap Fund?", "HDFC Mid Cap Fund - Direct Growth"),
        ("What is the HDFC Multi Cap NAV?", "HDFC Multi Cap Fund - Direct Growth"),
        ("Tell me about HDFC Gold ETF fund type", "HDFC Gold ETF Fund of Fund - Direct Plan Growth"),
        ("HDFC BSE Sensex Index tracking error", "HDFC BSE Sensex Index Fund - Direct Growth"),
        ("HDFC Short Term Opportunities duration", "HDFC Short Term Opportunities Fund - Direct Growth"),
        ("HDFC Focused Fund portfolio size", "HDFC Focused Fund - Direct Growth"),
        ("HDFC Nifty Next 50 benchmark", "HDFC Nifty Next 50 Index Fund - Direct Growth"),
        ("HDFC Pharma and Healthcare Fund category", "HDFC Pharma and Healthcare Fund - Direct Growth"),
        ("HDFC Balanced Advantage allocation", "HDFC Balanced Advantage Fund - Direct Growth"),
        ("HDFC Defence Fund holdings", "HDFC Defence Fund - Direct Growth"),
    ])
    def test_scheme_metadata_prefiltering(self, mock_chroma, mock_embedder, query, expected_canonical):
        """Queries mentioning specific schemes should trigger a 'where' filter in ChromaDB."""
        retrieve(query)
        
        # Verify collection.query was called with the correct 'where' filter
        mock_chroma.query.assert_called_once()
        call_kwargs = mock_chroma.query.call_args[1]
        assert "where" in call_kwargs
        assert call_kwargs["where"] == {"scheme_name": expected_canonical}

    def test_chunk_metadata_has_required_fields(self, mock_chroma, mock_embedder):
        """Every returned chunk should have similarity_score injected into metadata."""
        results = retrieve("test query")
        assert len(results) == 1
        assert "similarity_score" in results[0].metadata
        assert results[0].metadata["similarity_score"] == 0.95

    def test_score_threshold_filters_low_scores(self, mock_chroma, mock_embedder):
        """Chunks below the 0.65 threshold should be excluded."""
        # By default mock_chroma returns distances 0.1 (0.95) and 0.8 (0.60)
        # Threshold is 0.65, so only the first chunk should be returned.
        results = retrieve("test query", score_threshold=0.65)
        assert len(results) == 1
        
        results_strict = retrieve("test query", score_threshold=0.99)
        assert len(results_strict) == 0

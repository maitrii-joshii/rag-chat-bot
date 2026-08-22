"""Unit tests for src.generation.generator model configuration and fallback mechanism."""

from unittest.mock import MagicMock, patch
import pytest

from src.ingestion.loader import Document
from src.generation.generator import DEFAULT_MODEL, FALLBACK_MODEL, generate, NO_INFORMATION_RESPONSE


def make_chunk(text: str = "The expense ratio is 0.68% per annum.") -> Document:
    return Document(
        text=text,
        metadata={
            "scheme_name": "HDFC Small Cap Fund - Direct Growth",
            "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "fetch_date": "2026-08-05",
            "chunk_index": 0,
            "chunk_text": text,
            "similarity_score": 0.91,
        },
    )


def test_default_model_constants():
    """Verify default model and fallback model IDs."""
    assert DEFAULT_MODEL == "openai/gpt-oss-120b"
    assert FALLBACK_MODEL == "qwen/qwen3.6-27b"


def test_generate_no_chunks():
    """Empty chunks returns no-information fallback immediately without calling Groq."""
    ans = generate("What is the expense ratio?", chunks=[])
    assert ans == NO_INFORMATION_RESPONSE


@patch("src.generation.generator._get_groq_client")
def test_generate_primary_model_success(mock_get_client):
    """Primary model generates response successfully."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "The expense ratio of HDFC Small Cap Fund is 0.68% per annum. "
        "[Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth] "
        "Last updated from sources: 2026-08-05"
    )
    mock_completion = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_completion
    mock_get_client.return_value = mock_client

    ans = generate("What is the expense ratio?", chunks=[make_chunk()])

    assert "0.68%" in ans
    assert mock_client.chat.completions.create.call_count == 1
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "openai/gpt-oss-120b"


@patch("src.generation.generator._get_groq_client")
def test_generate_fallback_model_triggered(mock_get_client):
    """When primary model fails, fallback model is called and succeeds."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "The expense ratio of HDFC Small Cap Fund is 0.68% per annum. "
        "[Source: https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth] "
        "Last updated from sources: 2026-08-05"
    )
    mock_completion = MagicMock(choices=[mock_choice])

    # 1st call fails (primary), 2nd call succeeds (fallback)
    mock_client.chat.completions.create.side_effect = [
        RuntimeError("Primary model rate limit or unavailable"),
        mock_completion,
    ]
    mock_get_client.return_value = mock_client

    ans = generate("What is the expense ratio?", chunks=[make_chunk()])

    assert "0.68%" in ans
    assert mock_client.chat.completions.create.call_count == 2
    first_call_model = mock_client.chat.completions.create.call_args_list[0].kwargs["model"]
    second_call_model = mock_client.chat.completions.create.call_args_list[1].kwargs["model"]
    assert first_call_model == "openai/gpt-oss-120b"
    assert second_call_model == "qwen/qwen3.6-27b"


@patch("src.generation.generator._get_groq_client")
def test_generate_all_models_fail(mock_get_client):
    """When both primary and fallback models fail, RuntimeError is raised."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("All models failed")
    mock_get_client.return_value = mock_client

    with pytest.raises(RuntimeError, match="LLM generation failed"):
        generate("What is the expense ratio?", chunks=[make_chunk()])

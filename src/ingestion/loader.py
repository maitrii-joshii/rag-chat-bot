"""
Ingestion — Document Loader (Tasks 1.1 & 1.2)

Responsibilities:
  1. Enforce domain whitelist (groww.in, hdfcfund.com, amfiindia.com, sebi.gov.in).
  2. Fetch HTML via HTTP GET with appropriate headers, timeout, and retry logic.
  3. Parse with BeautifulSoup4 — extract scheme-specific sections, discard boilerplate.
  4. Return a Document with extracted text and enriched metadata.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# ── Domain Whitelist (Task 1.2) ───────────────────────────────────────────────
ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "groww.in",
        "hdfcfund.com",
        "amfiindia.com",
        "sebi.gov.in",
    }
)

# ── HTTP Configuration ────────────────────────────────────────────────────────
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
        "RAGMFBot/1.0 (+https://github.com/maitrii-joshii/rag-chat-bot)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",  # omit 'br' — brotli handled by requests/urllib3 automatically when brotli package is installed
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT: int = 30       # seconds per attempt
MAX_RETRIES: int = 3            # total attempts before giving up
RETRY_BACKOFF_BASE: float = 2.0 # seconds (exponential: 2, 4, 8)

# ── HTML tags whose content is always discarded (boilerplate) ─────────────────
_BOILERPLATE_TAGS: list[str] = [
    "script", "style", "noscript", "header", "footer", "nav",
    "aside", "form", "button", "svg", "iframe", "meta", "link",
    "advertisement", "cookie", "breadcrumb",
]

# ── CSS selectors to remove from Groww pages ─────────────────────────────────
_GROWW_REMOVE_SELECTORS: list[str] = [
    # Navigation & chrome
    "[class*='navbar']", "[class*='Navbar']",
    "[class*='header']", "[class*='Header']",
    "[class*='footer']", "[class*='Footer']",
    "[class*='sidebar']", "[class*='Sidebar']",
    # Ads & modals
    "[class*='banner']", "[class*='Banner']",
    "[class*='modal']", "[class*='Modal']",
    "[class*='popup']", "[class*='Popup']",
    "[class*='cookie']", "[class*='Cookie']",
    "[class*='toast']", "[class*='Toast']",
    # Social & share
    "[class*='social']", "[class*='Social']",
    "[class*='share']", "[class*='Share']",
    # Disclaimers that repeat on every page
    "[class*='disclaimer']", "[class*='Disclaimer']",
    # Breadcrumb
    "[class*='breadcrumb']", "[class*='Breadcrumb']",
    # Recommended / trending sections
    "[class*='recommended']", "[class*='Recommended']",
    "[class*='trending']", "[class*='Trending']",
    # App download
    "[class*='appDownload']", "[class*='app-download']",
    # Chat widgets
    "[id*='intercom']", "[id*='freshdesk']", "[id*='zendesk']",
]

# ── Groww: CSS selectors for content we WANT ─────────────────────────────────
_GROWW_CONTENT_SELECTORS: list[str] = [
    # Fund name / hero section
    "[class*='fundName']",
    "[class*='FundName']",
    "[class*='scheme-name']",
    "[class*='schemeName']",
    # NAV + returns summary
    "[class*='nav-']",
    "[class*='navValue']",
    "[class*='Nav']",
    "[class*='return']",
    "[class*='Return']",
    # Key facts / info table
    "[class*='keyFact']",
    "[class*='KeyFact']",
    "[class*='fundInfo']",
    "[class*='FundInfo']",
    "[class*='fundDetail']",
    "[class*='FundDetail']",
    "[class*='overview']",
    "[class*='Overview']",
    # Expense ratio / exit load
    "[class*='expenseRatio']",
    "[class*='expense']",
    "[class*='exitLoad']",
    "[class*='ExitLoad']",
    # Fund manager
    "[class*='fundManager']",
    "[class*='FundManager']",
    # Risk / category
    "[class*='risk']",
    "[class*='Risk']",
    "[class*='category']",
    "[class*='Category']",
    # Holdings / portfolio
    "[class*='holding']",
    "[class*='Holding']",
    "[class*='portfolio']",
    "[class*='Portfolio']",
    # SIP details
    "[class*='sip']",
    "[class*='SIP']",
    "[class*='minInvest']",
    # About section
    "[class*='about']",
    "[class*='About']",
]


@dataclass
class Document:
    """Lightweight document wrapper used throughout the RAG pipeline."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Public API ────────────────────────────────────────────────────────────────

def load_url(url: str, scheme_name: str) -> Document:
    """Fetch a scheme page and return a Document with extracted text + metadata.

    Tasks 1.1 (HTML Loader) and 1.2 (URL Whitelist) are implemented here.

    Args:
        url:         Full HTTPS URL of the scheme page (must be whitelisted).
        scheme_name: Human-readable scheme name attached to metadata.

    Returns:
        Document with extracted plain text and enriched metadata dict containing:
        ``source_url``, ``scheme_name``, ``document_type``, ``fetch_date``.

    Raises:
        ValueError: If the URL domain is not in ALLOWED_DOMAINS (Task 1.2).
        requests.HTTPError: If the server returns a non-2xx status after retries.
        requests.RequestException: For network-level failures after retries.
    """
    _validate_domain(url)  # Task 1.2 — whitelist enforcement

    html = _fetch_with_retry(url)
    text = _extract_text(html, url)
    fetch_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    metadata: dict[str, Any] = {
        "source_url": url,
        "scheme_name": scheme_name,
        "document_type": "scheme_page",
        "fetch_date": fetch_date,
    }

    logger.info(
        "Loaded %s — %d chars extracted",
        scheme_name,
        len(text),
    )
    return Document(text=text, metadata=metadata)


# ── Domain Validation (Task 1.2) ──────────────────────────────────────────────

def _validate_domain(url: str) -> None:
    """Raise ValueError if the URL's domain is not in ALLOWED_DOMAINS."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    if not any(
        domain == allowed or domain.endswith(f".{allowed}")
        for allowed in ALLOWED_DOMAINS
    ):
        raise ValueError(
            f"Domain '{domain}' is not in the allowed whitelist: {ALLOWED_DOMAINS}"
        )


# ── HTTP Fetch with Retry + Exponential Backoff ───────────────────────────────

def _fetch_with_retry(url: str) -> str:
    """GET a URL and return the response HTML, retrying on transient failures.

    Args:
        url: Validated, whitelisted URL.

    Returns:
        Response HTML as a string.

    Raises:
        requests.HTTPError / requests.RequestException after MAX_RETRIES.
    """
    session = requests.Session()
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            logger.debug("Fetched %s (attempt %d, status %d)", url, attempt, response.status_code)
            return response.text

        except requests.HTTPError as exc:
            # Don't retry on 4xx client errors — they won't recover
            if exc.response is not None and exc.response.status_code < 500:
                logger.error("Client error %d for %s — not retrying", exc.response.status_code, url)
                raise
            last_exc = exc

        except requests.RequestException as exc:
            last_exc = exc

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF_BASE ** attempt
            logger.warning(
                "Fetch attempt %d/%d failed for %s — retrying in %.1fs: %s",
                attempt, MAX_RETRIES, url, wait, last_exc,
            )
            time.sleep(wait)

    logger.error("All %d fetch attempts failed for %s", MAX_RETRIES, url)
    raise last_exc  # type: ignore[misc]


# ── HTML Text Extraction ──────────────────────────────────────────────────────

def _extract_text(html: str, url: str) -> str:
    """Parse HTML and extract meaningful text for ingestion.

    Strategy:
      1. Remove all boilerplate tags and Groww-specific noise selectors.
      2. Try to extract targeted content via known Groww CSS selectors.
      3. Fall back to full-body text extraction if targeted selectors yield < 200 chars.
      4. Clean up excessive whitespace.

    Args:
        html: Raw HTML response string.
        url:  Source URL (used to choose domain-specific extraction logic).

    Returns:
        Clean plain text ready for preprocessing.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Step 1 — Remove boilerplate tags entirely
    for tag_name in _BOILERPLATE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Step 2 — Remove Groww-specific noise selectors
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    if "groww.in" in domain:
        for selector in _GROWW_REMOVE_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

    # Step 3 — Try targeted extraction
    text = _targeted_extraction(soup, domain)

    # Step 4 — Fall back to full body if extraction yielded too little
    if len(text.strip()) < 200:
        logger.warning("Targeted extraction yielded < 200 chars — falling back to full body")
        body = soup.find("body") or soup
        text = _element_to_text(body)

    return text


def _targeted_extraction(soup: BeautifulSoup, domain: str) -> str:
    """Attempt to extract structured content from known page sections.

    For Groww pages: tries content selectors in order, collects all matches.
    For other domains: falls through to caller's fallback.
    """
    parts: list[str] = []

    if "groww.in" in domain:
        # Try each content selector and accumulate non-empty results
        seen_texts: set[str] = set()
        for selector in _GROWW_CONTENT_SELECTORS:
            for el in soup.select(selector):
                piece = _element_to_text(el).strip()
                if piece and piece not in seen_texts:
                    parts.append(piece)
                    seen_texts.add(piece)

    # Also always grab the main content area as a catch-all
    for main_selector in ["main", "[role='main']", "#main-content", ".main-content"]:
        main_el = soup.select_one(main_selector)
        if main_el:
            parts.append(_element_to_text(main_el))
            break

    return "\n\n".join(parts)


def _element_to_text(element: Tag | BeautifulSoup) -> str:
    """Convert a BeautifulSoup element to clean plain text.

    Handles:
      - <table> elements → formatted as pipe-separated text rows
      - All other elements → get_text with newline separator
    """
    parts: list[str] = []

    for child in element.children:
        if not isinstance(child, Tag):
            continue

        tag_name = child.name.lower() if child.name else ""

        if tag_name == "table":
            parts.append(_table_to_text(child))
        elif tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            heading_text = child.get_text(separator=" ", strip=True)
            if heading_text:
                parts.append(f"\n## {heading_text}\n")
        else:
            text = child.get_text(separator=" ", strip=True)
            if text:
                parts.append(text)

    return "\n".join(parts)


def _table_to_text(table: Tag) -> str:
    """Convert an HTML <table> element to a readable pipe-separated text block.

    Tables are preserved intact so the chunker can keep them as a single chunk.
    """
    rows: list[str] = []

    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        row_text = " | ".join(
            cell.get_text(separator=" ", strip=True) for cell in cells
        )
        if row_text.strip():
            rows.append(row_text)

    if not rows:
        return ""

    return "[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]"

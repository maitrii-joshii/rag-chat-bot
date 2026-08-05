/**
 * RAG Mutual Fund FAQ Assistant — Chat UI Script
 * Phase 0 scaffold — API endpoints wired in Phase 4.
 *
 * Responsibilities:
 *   1. Load example questions from GET /api/examples on page load.
 *   2. Handle form submission → POST /api/chat → render response.
 *   3. Render user and bot message bubbles with citations and footer.
 *   4. Show typing indicator while awaiting a response.
 *   5. Handle API errors gracefully.
 */

"use strict";

// ── Configuration ─────────────────────────────────────────────────────────────
const API_BASE = "";  // Empty = same origin; set to Railway URL in production.

// ── DOM References ────────────────────────────────────────────────────────────
const chatForm    = document.getElementById("chat-form");
const queryInput  = document.getElementById("query-input");
const sendBtn     = document.getElementById("send-btn");
const chatHistory = document.getElementById("chat-history");
const exampleList = document.getElementById("example-list");

// ── Initialisation ────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
});

/**
 * Fetch example questions and populate the example list.
 */
async function loadExamples() {
  try {
    const res  = await fetch(`${API_BASE}/api/examples`);
    const data = await res.json();

    (data.examples || []).forEach((q) => {
      const li  = document.createElement("li");
      const btn = document.createElement("button");
      btn.type        = "button";
      btn.textContent = q;
      btn.addEventListener("click", () => submitQuery(q));
      li.appendChild(btn);
      exampleList.appendChild(li);
    });
  } catch (err) {
    console.warn("Could not load examples:", err);
  }
}

// ── Form Submission ───────────────────────────────────────────────────────────
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;
  submitQuery(query);
  queryInput.value = "";
});

/**
 * Submit a query to POST /api/chat and render the result.
 * @param {string} query
 */
async function submitQuery(query) {
  appendMessage("user", query);
  setLoading(true);

  const typingEl = appendTypingIndicator();

  try {
    const res  = await fetch(`${API_BASE}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query }),
    });

    const data = await res.json();
    typingEl.remove();

    renderBotMessage(data);
  } catch (err) {
    typingEl.remove();
    appendMessage(
      "bot",
      "⚠️ Sorry, I couldn't reach the server. Please try again shortly.",
    );
    console.error("API error:", err);
  } finally {
    setLoading(false);
  }
}

// ── Rendering Helpers ─────────────────────────────────────────────────────────

/**
 * Render a bot response with optional citation and footer.
 * @param {{ answer: string, citation: object|null, last_updated: string }} data
 */
function renderBotMessage(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";

  // Answer bubble
  const bubble = document.createElement("div");
  bubble.className   = "bubble";
  bubble.textContent = data.answer || "No answer returned.";
  wrapper.appendChild(bubble);

  // Citation
  if (data.citation?.url) {
    const cite = document.createElement("div");
    cite.className = "citation";
    cite.innerHTML = `Source: <a href="${escapeHtml(data.citation.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(data.citation.scheme_name || data.citation.url)}</a>`;
    wrapper.appendChild(cite);
  }

  // Last updated footer
  if (data.last_updated && data.last_updated !== "N/A") {
    const footer = document.createElement("div");
    footer.className   = "footer-note";
    footer.textContent = `Last updated from sources: ${data.last_updated}`;
    wrapper.appendChild(footer);
  }

  chatHistory.appendChild(wrapper);
  scrollToBottom();
}

/**
 * Append a simple user or bot text message bubble.
 * @param {"user"|"bot"} role
 * @param {string} text
 */
function appendMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className   = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  chatHistory.appendChild(wrapper);
  scrollToBottom();
}

/**
 * Show a typing indicator (three animated dots) while waiting for the API.
 * @returns {HTMLElement} The typing indicator element (caller must remove it).
 */
function appendTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  wrapper.appendChild(indicator);

  chatHistory.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function setLoading(isLoading) {
  sendBtn.disabled    = isLoading;
  queryInput.disabled = isLoading;
}

function scrollToBottom() {
  chatHistory.scrollTop = chatHistory.scrollHeight;
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * RAG Mutual Fund FAQ Assistant — Chat UI Script (Task 4.8)
 *
 * Responsibilities:
 *   1. Generate a per-session ID for request tracing.
 *   2. Poll GET /api/health on load — update status chip.
 *   3. Fetch GET /api/examples — render clickable sidebar buttons.
 *   4. Handle form submit / Enter key → POST /api/chat.
 *   5. Render user bubbles, typing indicator, and bot responses.
 *   6. Display query_type badge, citation chip, last-updated footer.
 *   7. Handle HTTP 429 (rate limit) with Retry-After countdown toast.
 *   8. Handle all non-factual intents with appropriate UI styling.
 *   9. Character counter with colour feedback.
 *  10. Auto-scroll + welcome screen hide on first message.
 *  11. XSS-safe rendering via escapeHtml() throughout.
 */

"use strict";

/* ── Configuration ─────────────────────────────────────────────────────────── */
/** Set to Railway backend URL in production, empty string for same-origin. */
const API_BASE = "";

/* ── Session ID ────────────────────────────────────────────────────────────── */
/** Lightweight UUID-v4-like generator — no crypto dependency needed. */
function generateSessionId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

const SESSION_ID = generateSessionId();

/* ── DOM References ────────────────────────────────────────────────────────── */
const chatForm       = document.getElementById("chat-form");
const queryInput     = document.getElementById("query-input");
const sendBtn        = document.getElementById("send-btn");
const chatHistory    = document.getElementById("chat-history");
const exampleList    = document.getElementById("example-list");
const welcomeScreen  = document.getElementById("welcome-screen");
const charCounter    = document.getElementById("char-counter");
const toastContainer = document.getElementById("toast-container");
const healthText     = document.getElementById("health-status-text");

let welcomeHidden = false;  // Track if welcome screen has been dismissed

/* ── Initialisation ────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
  checkHealth();
  initCharCounter();
  queryInput.focus();
});

/* ── Health Check ──────────────────────────────────────────────────────────── */
async function checkHealth() {
  const dot = document.querySelector(".chip-dot");
  try {
    const res  = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();

    if (data.status === "healthy") {
      dot.className = "chip-dot chip-dot--green";
      healthText.textContent = "Ready";
    } else {
      dot.className = "chip-dot chip-dot--yellow";
      healthText.textContent = "Service starting up…";
    }
  } catch {
    dot.className = "chip-dot chip-dot--red";
    healthText.textContent = "Server offline";
  }
}

/* ── Load Example Questions ────────────────────────────────────────────────── */
async function loadExamples() {
  try {
    const res  = await fetch(`${API_BASE}/api/examples`);
    const data = await res.json();

    exampleList.innerHTML = "";  // Clear skeletons

    (data.examples || []).forEach((q) => {
      const li  = document.createElement("li");
      const btn = document.createElement("button");
      btn.type        = "button";
      btn.className   = "example-btn";
      btn.textContent = q;
      btn.title       = q;
      btn.addEventListener("click", () => {
        queryInput.value = q;
        updateCharCounter(q.length);
        chatForm.requestSubmit();
        queryInput.focus();
      });
      li.appendChild(btn);
      exampleList.appendChild(li);
    });
  } catch (err) {
    console.warn("Could not load examples:", err);
    exampleList.innerHTML = '<li style="font-size:0.75rem;color:var(--text-faint);padding:0.25rem 0;">Examples unavailable</li>';
  }
}

/* ── Character Counter ──────────────────────────────────────────────────────── */
function initCharCounter() {
  queryInput.addEventListener("input", () => {
    updateCharCounter(queryInput.value.length);
  });
}

function updateCharCounter(len) {
  const max = 500;
  charCounter.textContent = `${len} / ${max}`;
  charCounter.className = "char-counter";
  if (len >= max * 0.9) charCounter.classList.add("danger");
  else if (len >= max * 0.7) charCounter.classList.add("warn");
}

/* ── Form Submission ────────────────────────────────────────────────────────── */
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) { queryInput.focus(); return; }
  submitQuery(query);
  queryInput.value = "";
  updateCharCounter(0);
});

/* ── Main Query Submission ─────────────────────────────────────────────────── */
/**
 * Send a query to the API and render the result.
 * @param {string} query
 */
async function submitQuery(query) {
  // Hide welcome screen on first message
  if (!welcomeHidden) {
    welcomeScreen.classList.add("hidden");
    welcomeHidden = true;
  }

  // Render user message
  appendUserMessage(query);
  setLoading(true);
  const typingEl = appendTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query, session_id: SESSION_ID }),
    });

    typingEl.remove();

    // Handle rate limit
    if (res.status === 429) {
      const data = await res.json().catch(() => ({}));
      const retryAfter = res.headers.get("Retry-After") || "60";
      showToast(
        `⏳ Too many requests. Please wait ${retryAfter}s before trying again.`,
        "warning",
        4000
      );
      appendBotError("I'm receiving too many requests right now. Please wait a moment and try again.");
      return;
    }

    // Handle server errors
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      appendBotError(errData.detail || "An unexpected error occurred. Please try again.");
      return;
    }

    const data = await res.json();
    renderBotMessage(data);

  } catch (err) {
    typingEl.remove();
    appendBotError("⚠️ Couldn't reach the server. Please check your connection and try again.");
    console.error("API error:", err);
  } finally {
    setLoading(false);
    scrollToBottom();
    queryInput.focus();
  }
}

/* ── Rendering Functions ────────────────────────────────────────────────────── */

/**
 * Render a user message bubble.
 * @param {string} text
 */
function appendUserMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "message user";
  wrapper.setAttribute("role", "listitem");

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "You";
  wrapper.appendChild(meta);

  const bubble = document.createElement("div");
  bubble.className   = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  chatHistory.appendChild(wrapper);
  scrollToBottom();
}

/**
 * Render a bot response with badge, answer, citation, and footer.
 * @param {{ answer: string, citation: object|null, last_updated: string, query_type: string }} data
 */
function renderBotMessage(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.setAttribute("role", "listitem");

  // Meta row
  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "HDFC MF Assistant";
  wrapper.appendChild(meta);

  // Query type badge
  const badge = makeBadge(data.query_type);
  wrapper.appendChild(badge);

  // Answer bubble
  const bubble = document.createElement("div");
  bubble.className   = "bubble";
  bubble.textContent = data.answer || "No answer returned.";
  wrapper.appendChild(bubble);

  // Citation chip (factual responses only)
  if (data.citation?.url) {
    const cite = document.createElement("div");
    cite.className = "citation";
    cite.innerHTML =
      `<span class="citation-icon">🔗</span>` +
      `<span>Source: <a href="${escapeHtml(data.citation.url)}" ` +
      `target="_blank" rel="noopener noreferrer">` +
      `${escapeHtml(data.citation.scheme_name || data.citation.url)}</a></span>`;
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
 * Render a simple error bot message.
 * @param {string} text
 */
function appendBotError(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.setAttribute("role", "listitem");

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "HDFC MF Assistant";
  wrapper.appendChild(meta);

  const bubble = document.createElement("div");
  bubble.className   = "bubble";
  bubble.style.color = "var(--error)";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  chatHistory.appendChild(wrapper);
  scrollToBottom();
}

/**
 * Show an animated typing indicator (3 bouncing dots).
 * @returns {HTMLElement} The indicator element — caller must remove it.
 */
function appendTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "HDFC MF Assistant";
  wrapper.appendChild(meta);

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.setAttribute("aria-label", "Assistant is typing");
  indicator.innerHTML = "<span></span><span></span><span></span>";
  bubble.appendChild(indicator);
  wrapper.appendChild(bubble);

  chatHistory.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

/* ── Badge Helper ───────────────────────────────────────────────────────────── */

/** Badge labels and icons per query type */
const BADGE_CONFIG = {
  factual:      { label: "✅ Factual",      cls: "badge--factual" },
  advisory:     { label: "🚫 Advisory",     cls: "badge--advisory" },
  comparison:   { label: "⚖️ Comparison",   cls: "badge--comparison" },
  prediction:   { label: "🔮 Prediction",   cls: "badge--prediction" },
  buy_sell:     { label: "🛒 Buy / Sell",   cls: "badge--buy_sell" },
  out_of_scope: { label: "❓ Out of Scope", cls: "badge--out_of_scope" },
  pii_blocked:  { label: "🔒 PII Blocked",  cls: "badge--pii_blocked" },
};

/**
 * Create a query-type badge element.
 * @param {string} queryType
 * @returns {HTMLElement}
 */
function makeBadge(queryType) {
  const cfg = BADGE_CONFIG[queryType] || { label: queryType, cls: "" };
  const badge = document.createElement("div");
  badge.className = `query-type-badge ${cfg.cls}`;
  badge.textContent = cfg.label;
  badge.setAttribute("aria-label", `Query type: ${queryType}`);
  return badge;
}

/* ── Toast Notifications ────────────────────────────────────────────────────── */

/**
 * Show a transient toast notification.
 * @param {string} message
 * @param {"error"|"warning"|"info"} type
 * @param {number} durationMs
 */
function showToast(message, type = "info", durationMs = 3000) {
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "opacity 0.3s, transform 0.3s";
    setTimeout(() => toast.remove(), 350);
  }, durationMs);
}

/* ── UI Utilities ───────────────────────────────────────────────────────────── */

function setLoading(isLoading) {
  sendBtn.disabled    = isLoading;
  queryInput.disabled = isLoading;
}

function scrollToBottom() {
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g,  "&amp;")
    .replace(/</g,  "&lt;")
    .replace(/>/g,  "&gt;")
    .replace(/"/g,  "&quot;")
    .replace(/'/g,  "&#39;");
}

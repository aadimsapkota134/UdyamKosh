const API = "http://localhost:5000/api";

// ── Fetch helpers ──────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

const apiGet    = (path)         => apiFetch(path);
const apiPost   = (path, body)   => apiFetch(path, { method: "POST",  body: JSON.stringify(body) });
const apiPatch  = (path, body)   => apiFetch(path, { method: "PATCH", body: JSON.stringify(body) });

// ── Toast ──────────────────────────────────────────────────
function toast(msg, error = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.background = error ? "#A32D2D" : "#1A1A18";
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 3000);
}

// ── Badge helper ───────────────────────────────────────────
const STATUS_CLASS = {
  submitted:    "badge-review",
  under_review: "badge-review",
  approved:     "badge-approved",
  rejected:     "badge-rejected",
  disbursed:    "badge-disbursed",
  active:       "badge-active",
  closed:       "badge-closed",
  defaulted:    "badge-overdue",
};

function badge(status) {
  const cls = STATUS_CLASS[status] || "badge-review";
  return `<span class="badge ${cls}">${status.replace("_", " ")}</span>`;
}

// ── Format helpers ─────────────────────────────────────────
function fmtRs(n)   { return "Rs " + Number(n).toLocaleString("en-IN"); }
function fmtDate(d) { return d ? d.slice(0, 10) : "—"; }

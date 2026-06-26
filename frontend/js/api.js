/* =====================================================================
   TravelAI — Frontend API Client
   All backend communication goes through this module.
   ===================================================================== */

const API_BASE = window.API_BASE || "http://localhost:8000/api/v1";

// ── Token management ────────────────────────────────────────────────
const Auth = {
  getToken()        { return localStorage.getItem("tai_token"); },
  setToken(t)       { localStorage.setItem("tai_token", t); },
  removeToken()     { localStorage.removeItem("tai_token"); localStorage.removeItem("tai_user"); },
  getUser()         { try { return JSON.parse(localStorage.getItem("tai_user")); } catch { return null; } },
  setUser(u)        { localStorage.setItem("tai_user", JSON.stringify(u)); },
  isLoggedIn()      { return !!this.getToken(); },
  isPro()           { const u = this.getUser(); return u?.is_pro === true; },
  requireAuth()     { if (!this.isLoggedIn()) { window.location.href = "/login.html"; return false; } return true; },
};

// ── HTTP helper ─────────────────────────────────────────────────────
async function api(path, options = {}) {
  const token = Auth.getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  let data;
  try { data = await resp.json(); } catch { data = {}; }

  if (!resp.ok) {
    const msg = data?.detail?.message || data?.detail || "Something went wrong.";
    const err = new Error(msg);
    err.status           = resp.status;
    err.upgradeRequired  = data?.detail?.upgrade_required || false;
    throw err;
  }
  return data;
}

// ── Auth API ────────────────────────────────────────────────────────
const AuthAPI = {
  async register(email, username, password, fullName) {
    const data = await api("/auth/register", { method: "POST", body: { email, username, password, full_name: fullName } });
    Auth.setToken(data.access_token);
    Auth.setUser(data.user);
    return data;
  },
  async login(email, password) {
    const data = await api("/auth/login", { method: "POST", body: { email, password } });
    Auth.setToken(data.access_token);
    Auth.setUser(data.user);
    return data;
  },
  async me() {
    const data = await api("/auth/me");
    Auth.setUser(data);
    return data;
  },
  async updateProfile(body) {
    const data = await api("/auth/profile", { method: "PUT", body });
    Auth.setUser(data);
    return data;
  },
  logout() { Auth.removeToken(); window.location.href = "/login.html"; },
};

// ── Chat API ────────────────────────────────────────────────────────
const ChatAPI = {
  async send(message, sessionId) {
    return api("/chat/message", { method: "POST", body: { message, session_id: sessionId } });
  },
  async history(sessionId, limit = 50) {
    const qs = sessionId ? `?session_id=${sessionId}&limit=${limit}` : `?limit=${limit}`;
    return api(`/chat/history${qs}`);
  },
  async sessions() { return api("/chat/sessions"); },
  async clearHistory(sessionId) {
    const qs = sessionId ? `?session_id=${sessionId}` : "";
    return api(`/chat/history${qs}`, { method: "DELETE" });
  },
};

// ── Planner API ─────────────────────────────────────────────────────
const PlannerAPI = {
  async generate(destination, days, budget, tripType, preferences, title) {
    return api("/planner/generate", { method: "POST", body: { destination, days, budget, trip_type: tripType, preferences, title } });
  },
  async listTrips() { return api("/planner/trips"); },
  async getTrip(id) { return api(`/planner/trips/${id}`); },
  async updateStatus(id, status) { return api(`/planner/trips/${id}/status`, { method: "PUT", body: { status } }); },
  async deleteTrip(id) { return api(`/planner/trips/${id}`, { method: "DELETE" }); },
};

// ── Recommendations API ─────────────────────────────────────────────
const RecommendAPI = {
  async suggest(country, budget, tripType, interests, topN = 10) {
    return api("/recommendations/suggest", { method: "POST", body: { country, budget, trip_type: tripType, interests, top_n: topN } });
  },
  async getMeta() { return api("/recommendations/meta"); },
  async listDestinations(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return api(`/recommendations/destinations${qs ? "?" + qs : ""}`);
  },
  async listCountries() { return api("/recommendations/countries"); },
};

// ── Subscription API ────────────────────────────────────────────────
const SubAPI = {
  async getPlans()  { return api("/subscription/plans"); },
  async getStatus() { return api("/subscription/status"); },
  async checkout(planId, cardNumber, cardHolder, expiry, cvv) {
    return api("/subscription/checkout", { method: "POST", body: { plan_id: planId, card_number: cardNumber, card_holder: cardHolder, expiry, cvv } });
  },
  async cancel(reason) { return api("/subscription/cancel", { method: "POST", body: { reason } }); },
};

// ── UI Helpers ──────────────────────────────────────────────────────
function showToast(msg, type = "info") {
  const el   = document.createElement("div");
  const cols  = { success: "#10b981", error: "#ef4444", info: "#3b82f6", warning: "#f59e0b" };
  el.style.cssText = `position:fixed;bottom:24px;right:24px;background:${cols[type]||cols.info};color:#fff;padding:14px 22px;border-radius:12px;font-size:14px;font-weight:600;z-index:9999;box-shadow:0 8px 32px rgba(0,0,0,.25);animation:fadeInUp .3s ease;max-width:360px`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function setLoadingBtn(btn, loading, text) {
  if (loading) { btn.disabled = true; btn._orig = btn.innerHTML; btn.innerHTML = `<span class="spinner"></span> ${text||"Loading…"}`; }
  else         { btn.disabled = false; btn.innerHTML = btn._orig || text || "Submit"; }
}

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function budgetLabel(b) {
  return { low: "💚 Budget", medium: "💛 Mid-range", high: "💎 Luxury" }[b] || b;
}

// ── Navigation helpers ──────────────────────────────────────────────
function initNav() {
  const user = Auth.getUser();
  const navUser = document.getElementById("nav-user");
  const navLogin = document.getElementById("nav-login");
  if (navUser) navUser.style.display = user ? "flex" : "none";
  if (navLogin) navLogin.style.display = user ? "none" : "flex";
  const nameEl = document.getElementById("nav-username");
  if (nameEl && user) nameEl.textContent = user.username || user.email;
  const proEl = document.getElementById("nav-pro-badge");
  if (proEl) proEl.style.display = user?.is_pro ? "inline-block" : "none";
  const logoutBtn = document.getElementById("nav-logout");
  if (logoutBtn) logoutBtn.addEventListener("click", () => AuthAPI.logout());
}

window.Auth = Auth;
window.AuthAPI = AuthAPI;
window.ChatAPI = ChatAPI;
window.PlannerAPI = PlannerAPI;
window.RecommendAPI = RecommendAPI;
window.SubAPI = SubAPI;
window.showToast = showToast;
window.setLoadingBtn = setLoadingBtn;
window.formatDate = formatDate;
window.budgetLabel = budgetLabel;
window.initNav = initNav;

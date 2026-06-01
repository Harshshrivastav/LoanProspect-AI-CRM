// src/api/client.js
const BASE = "/api";

async function apiFetch(path, options = {}) {
  const { body, method = body ? "POST" : "GET", ...rest } = options;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
    ...rest,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const d = await res.json();
      detail = d.detail || d.message || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const getHealth = () => apiFetch("/health");
export const getCustomers = (page = 1, perPage = 20) =>
  apiFetch(`/customers?page=${page}&per_page=${perPage}`);
export const getCustomer = (id) => apiFetch(`/customers/${id}`);
export const getProspects = (limit = 20) =>
  apiFetch(`/prospects?limit=${limit}`);
export const getDynamicFactors = () =>
  apiFetch("/prospects/factors");
export const recalculateProspects = (focus, risk) =>
  apiFetch("/prospects/recalculate", {
    body: { campaign_focus: focus, risk_appetite: risk }
  });
export const getProspect = (id) => apiFetch(`/prospects/${id}`);
export const scoreCustomer = (customerId) =>
  apiFetch("/prospects/score", { body: { customer_id: customerId } });
export const analyzeCustomerWithCrew = (customerId) =>
  apiFetch(`/prospects/analyze/${customerId}`, { method: "POST" });
export const getTransactions = (customerId, days = 90) =>
  apiFetch(`/transactions/${customerId}?days=${days}`);
export const getCampaigns = () => apiFetch("/campaigns");
export const getCampaign = (id) => apiFetch(`/campaigns/${id}`);
export const createCampaign = (data) => apiFetch("/campaigns", { body: data });
export const approveCampaign = (campaignId) =>
  apiFetch("/campaigns/approve", { body: { campaign_id: campaignId } });
export const runBulkOutreach = (data) =>
  apiFetch("/campaigns/run-bulk-outreach", { body: data });
export const generateMessage = (
  customerId,
  productType = "personal_loan",
  tone = "friendly",
  channel = "whatsapp",
) =>
  apiFetch("/message/generate", {
    body: { customer_id: customerId, product_type: productType, tone, channel },
  });
export const generateBulkMessages = (customerIds, productType, tone) =>
  apiFetch("/message/bulk", {
    body: { customer_ids: customerIds, product_type: productType, tone },
  });
export const approveMessage = (outreachId) =>
  apiFetch("/message/approve", { body: { outreach_id: outreachId } });
export const getChatSessions = () => apiFetch("/chat/sessions");
export const createChatSession = (
  title = "New Conversation",
  customerContext = null,
) =>
  apiFetch("/chat/sessions", {
    body: { title, customer_context: customerContext },
  });
export const getChatMessages = (sessionId) =>
  apiFetch(`/chat/sessions/${sessionId}/messages`);
export const renameSession = (sessionId, title) =>
  apiFetch(`/chat/sessions/${sessionId}/rename`, {
    method: "PATCH",
    body: { title },
  });
export const archiveSession = (sessionId) =>
  apiFetch(`/chat/sessions/${sessionId}/archive`, { method: "PATCH" });
export const pinSession = (sessionId, pinned = true) =>
  apiFetch(`/chat/sessions/${sessionId}/pin?pinned=${pinned}`, {
    method: "PATCH",
  });
export const deleteSession = (sessionId) =>
  apiFetch(`/chat/sessions/${sessionId}`, { method: "DELETE" });
export const getAuditLogs = (limit = 100, entityId = null) =>
  apiFetch(`/audit?limit=${limit}${entityId ? `&entity_id=${entityId}` : ""}`);
export const getAgentStatus = () => apiFetch("/agent/status");
export const updateAgentConfig = (apiKey, model = "gemini-2.5-flash") =>
  apiFetch("/agent/config", {
    method: "POST",
    body: { gemini_api_key: apiKey, gemini_model: model },
  });


// Streaming chat — AsyncGenerator of parsed NDJSON events
export async function* streamChat(
  message,
  sessionId = null,
  customerContext = null,
  mode = "auto",
) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      customer_context: customerContext,
      mode,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const d = await res.json();
      detail = d.detail || detail;
    } catch {}
    yield { type: "error", error: detail };
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        yield JSON.parse(line);
      } catch {}
    }
  }
}

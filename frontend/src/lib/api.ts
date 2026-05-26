const API_BASE = import.meta.env.VITE_API_URL ?? "/backend";

export interface DetectionResult {
  id: number | null;
  fake: boolean;
  confidence: number;
  reason: string;
  model: string;
  labels: { label: string; score: number }[];
  type: "text" | "image" | "url";
  content_preview?: string | null;
  latency_ms?: number | null;
  cached?: boolean;
}

export interface DetectionRecord {
  id: number;
  type: string;
  content_preview: string;
  fake: boolean;
  confidence: number;
  reason: string;
  model: string;
  source: string | null;
  filename: string | null;
  latency_ms?: number | null;
  cached?: boolean;
  created_at: string;
}

export interface HistoryResponse {
  items: DetectionRecord[];
  total: number;
}

export interface StatsResponse {
  scanned_today: number;
  threats_total: number;
  threats_today: number;
  fake_rate_percent: number;
  recent_count: number;
  by_type: Record<string, number>;
  cache_hits?: number;
}

export interface AppSettings {
  confidence_threshold: number;
  use_llm?: boolean | null;
}

export interface BatchDetectionResponse {
  results: DetectionResult[];
  total: number;
}

export type DetectOptions = {
  source?: string;
  confidence_threshold?: number;
};

let _csrfToken: string | null = null;

async function getCsrfToken(): Promise<string> {
  if (_csrfToken) return _csrfToken;
  const res = await fetch(`${API_BASE}/auth/csrf-token`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch CSRF token");
  const data = await res.json();
  _csrfToken = data.csrf_token;
  return _csrfToken;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  init = init || {};
  // Always send cookies
  (init as RequestInit).credentials = "include";
  // If mutating request, ensure CSRF header
  const method = (init as RequestInit).method || "GET";
  // Attach tenant header from localStorage if present
  const tenantId = localStorage.getItem("tenant_id");
  if (tenantId) {
    (init as RequestInit).headers = {
      ...(init as RequestInit).headers,
      "X-Tenant-Id": tenantId,
    };
  }
  if (method !== "GET" && method !== "HEAD") {
    const csrf = await getCsrfToken();
    (init as RequestInit).headers = {
      ...(init as RequestInit).headers,
      "X-CSRF-Token": csrf,
    };
  }
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail ?? err)
    );
  }
  return res.json() as Promise<T>;
}

function bodyWithThreshold(
  payload: Record<string, unknown>,
  opts?: DetectOptions
) {
  if (opts?.confidence_threshold != null) {
    payload.confidence_threshold = opts.confidence_threshold;
  }
  return payload;
}

export function detectText(text: string, opts?: DetectOptions) {
  return request<DetectionResult>("/detect/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      bodyWithThreshold({ text, source: opts?.source ?? "manual" }, opts)
    ),
  });
}

export function detectUrl(url: string, opts?: DetectOptions) {
  return request<DetectionResult>("/detect/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyWithThreshold({ url }, opts)),
  });
}

export function detectTextBatch(texts: string[], opts?: DetectOptions) {
  return request<BatchDetectionResponse>("/detect/text/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(
      bodyWithThreshold({ texts, source: opts?.source ?? "batch" }, opts)
    ),
  });
}

export function detectImage(file: File, opts?: DetectOptions) {
  const form = new FormData();
  form.append("file", file);
  const q =
    opts?.confidence_threshold != null
      ? `?confidence_threshold=${opts.confidence_threshold}`
      : "";
  return request<DetectionResult>(`/detect/image${q}`, {
    method: "POST",
    body: form,
  });
}

export function fetchHistory(params?: {
  skip?: number;
  limit?: number;
  fake_only?: boolean;
  type?: string;
}) {
  const q = new URLSearchParams();
  if (params?.skip != null) q.set("skip", String(params.skip));
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.fake_only != null) q.set("fake_only", String(params.fake_only));
  if (params?.type) q.set("type", params.type);
  const qs = q.toString();
  return request<HistoryResponse>(`/history${qs ? `?${qs}` : ""}`);
}

export function exportHistoryUrl(format: "json" | "csv" = "json") {
  return `${API_BASE}/history/export?format=${format}`;
}

export function fetchStats() {
  return request<StatsResponse>("/stats");
}

export function fetchSettings() {
  return request<AppSettings>("/settings");
}

export function updateSettings(settings: AppSettings) {
  return request<AppSettings>("/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

export function fetchHealth() {
  return request<{
    status: string;
    text_model_loaded: boolean;
    image_model_loaded: boolean;
    image_ai_model_loaded: boolean;
    gemini_configured: boolean;
    use_llm: boolean;
    cache_enabled: boolean;
    rate_limit_per_minute: number;
  }>("/health");
}

export async function signupUser(payload: { username: string; email?: string; password: string; tenant_id: number }) {
  const res = await request<{ user_id?: number }>("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  // After signup, fetch CSRF token (cookies set by server)
  await getCsrfToken();
  return res;
}

export async function loginUser(payload: { username: string; password: string }) {
  const res = await request<{ status?: string }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await getCsrfToken();
  return res;
}

export async function refreshToken() {
  const res = await request<{ status?: string }>("/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // server will validate refresh cookie, no body required
  });
  await getCsrfToken();
  return res;
}

export async function logout() {
  const res = await request<{ revoked: boolean }>("/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // server will read refresh cookie
  });
  return res;
}

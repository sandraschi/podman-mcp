/**
 * REST bridge to podman-mcp backend (proxied via Vite in dev).
 */

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  kind: string;
  detail: string;
  meta?: Record<string, unknown>;
}

export interface LogsQueryResponse {
  entries: LogEntry[];
  total: number;
  limit: number;
  offset: number;
  max_entries: number;
  sort: string;
}

export interface LogStats {
  total: number;
  max_entries: number;
  rotation: string;
  by_level: Record<string, number>;
  by_kind: Record<string, number>;
  oldest: string | null;
  newest: string | null;
}

export interface LogQueryParams {
  limit?: number;
  offset?: number;
  level?: string;
  kind?: string;
  search?: string;
  sort?: "asc" | "desc";
  after_id?: string;
}

export interface LlmSettings {
  provider: string;
  model: string;
  endpoint: string;
}

export interface LlmProvider {
  type: string;
  base_url: string;
  models: string[];
  reachable: boolean;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.PROD ? "http://127.0.0.1:10807" : "");
const API = `${API_BASE}/api`;
const LLM_KEY = "podman-mcp-llm-settings";

const DEFAULT_ENDPOINTS: Record<string, string> = {
  ollama: "http://127.0.0.1:11434",
  lmstudio: "http://127.0.0.1:1234",
};

export function getLlmSettings(): LlmSettings {
  try {
    const raw = localStorage.getItem(LLM_KEY);
    if (raw) return JSON.parse(raw) as LlmSettings;
  } catch {
    /* ignore */
  }
  return {
    provider: "ollama",
    model: "",
    endpoint: DEFAULT_ENDPOINTS.ollama,
  };
}

export function setLlmSettings(settings: LlmSettings): void {
  localStorage.setItem(LLM_KEY, JSON.stringify(settings));
}

function buildLogParams(params: LogQueryParams): string {
  const q = new URLSearchParams();
  if (params.limit != null) q.set("limit", String(params.limit));
  if (params.offset != null) q.set("offset", String(params.offset));
  if (params.level) q.set("level", params.level);
  if (params.kind) q.set("kind", params.kind);
  if (params.search) q.set("search", params.search);
  if (params.sort) q.set("sort", params.sort);
  if (params.after_id) q.set("after_id", params.after_id);
  return q.toString();
}

export async function getHealth(): Promise<{ status: string; service?: string }> {
  const r = await fetch(`${API}/health`);
  if (!r.ok) throw new Error(`Health check failed: ${r.status}`);
  return r.json();
}

export async function getLlmProviders(refresh = false): Promise<LlmProvider[]> {
  const q = refresh ? "?refresh=1" : "";
  const r = await fetch(`${API}/llm/providers${q}`);
  if (!r.ok) throw new Error(`LLM providers failed: ${r.status}`);
  const body = await r.json();
  return body.providers ?? [];
}

export async function queryLogs(params: LogQueryParams = {}): Promise<LogsQueryResponse> {
  const qs = buildLogParams(params);
  const r = await fetch(`${API}/logs${qs ? `?${qs}` : ""}`);
  if (!r.ok) throw new Error(`Logs query failed: ${r.status}`);
  return r.json();
}

export async function getLogStats(): Promise<LogStats> {
  const r = await fetch(`${API}/logs/stats`);
  if (!r.ok) throw new Error(`Log stats failed: ${r.status}`);
  return r.json();
}

export async function clearLogs(): Promise<void> {
  const r = await fetch(`${API}/logs`, { method: "DELETE" });
  if (!r.ok) throw new Error(`Clear logs failed: ${r.status}`);
}

export async function getComposeProjects(all = false): Promise<{ projects: any[]; total: number }> {
  const r = await fetch(`${API}/compose/projects?all=${all}`);
  if (!r.ok) throw new Error(`Compose projects failed: ${r.status}`);
  return r.json();
}

export async function getComposePs(project: string): Promise<{ containers: any[]; total: number }> {
  const r = await fetch(`${API}/compose/ps?project=${encodeURIComponent(project)}`);
  if (!r.ok) throw new Error(`Compose ps failed: ${r.status}`);
  return r.json();
}

export async function composeUp(project: string, build = false): Promise<{ success: boolean; message?: string }> {
  const r = await fetch(`${API}/compose/up`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ project, build }) });
  return r.json();
}

export async function composeDown(project: string, volumes = false): Promise<{ success: boolean; message?: string }> {
  const r = await fetch(`${API}/compose/down`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ project, volumes }) });
  return r.json();
}

export async function getComposeLogs(project: string, tail = 50): Promise<{ success: boolean; output?: string; logs?: string }> {
  const r = await fetch(`${API}/compose/logs?project=${encodeURIComponent(project)}&tail=${tail}`);
  return r.json();
}

export async function analyzeComposeFile(filePath: string): Promise<any> {
  const r = await fetch(`${API}/compose/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_path: filePath }),
  });
  return r.json();
}

export async function getComposeConfig(project: string): Promise<{ success: boolean; config?: string }> {
  const r = await fetch(`${API}/compose/config?project=${encodeURIComponent(project)}`);
  return r.json();
}

export async function downloadLogsExport(
  format: "json" | "csv",
  filters: Omit<LogQueryParams, "limit" | "offset" | "after_id"> = {},
): Promise<void> {
  const q = buildLogParams({ ...filters, limit: undefined, offset: undefined });
  const r = await fetch(`${API}/logs/export?format=${format}${q ? `&${q}` : ""}`);
  if (!r.ok) throw new Error(`Export failed: ${r.status}`);
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `podman-mcp-logs.${format}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

import {
  API_ENDPOINTS,
  type AuthRequest,
  type AuthResponse,
  type OperationsOverviewResponse,
  type PauseResumeScanResponse,
  type ProgramDiscoveryResponse,
  type ReportsAnalyticsResponse,
  type ReportsResponse,
  type ScanStatusResponse,
  type SearchResponse,
  type StopScanResponse,
  type StartScanRequest,
  type StartScanResponse,
  type StatsResponse,
} from "@/lib/api-contract";
import { getToken } from "@/lib/auth";

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

function resolveApiBase(): string {
  if (configuredApiBase) {
    return configuredApiBase.replace(/\/+$/, "");
  }
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

async function request<T>(path: string, init?: RequestInit, auth = false): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = getToken();
    if (!token) {
      throw new Error("Authentication required.");
    }
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data && typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : `Request failed (${res.status})`;
    throw new Error(detail);
  }

  return data as T;
}

export async function register(payload: AuthRequest): Promise<AuthResponse> {
  return request<AuthResponse>(API_ENDPOINTS.register, { method: "POST", body: JSON.stringify(payload) });
}

export async function login(payload: AuthRequest): Promise<AuthResponse> {
  return request<AuthResponse>(API_ENDPOINTS.login, { method: "POST", body: JSON.stringify(payload) });
}

export async function startScan(payload: StartScanRequest): Promise<StartScanResponse> {
  return request<StartScanResponse>(API_ENDPOINTS.startScan, { method: "POST", body: JSON.stringify(payload) }, true);
}

export async function getScanStatus(scanId: string): Promise<ScanStatusResponse> {
  return request<ScanStatusResponse>(API_ENDPOINTS.scanStatus(scanId), { method: "GET" }, true);
}

export async function stopScan(scanId: string): Promise<StopScanResponse> {
  return request<StopScanResponse>(API_ENDPOINTS.stopScan(scanId), { method: "POST" }, true);
}

export async function pauseScan(scanId: string): Promise<PauseResumeScanResponse> {
  return request<PauseResumeScanResponse>(API_ENDPOINTS.pauseScan(scanId), { method: "POST" }, true);
}

export async function resumeScan(scanId: string): Promise<PauseResumeScanResponse> {
  return request<PauseResumeScanResponse>(API_ENDPOINTS.resumeScan(scanId), { method: "POST" }, true);
}

export async function discoverProgram(): Promise<ProgramDiscoveryResponse> {
  return request<ProgramDiscoveryResponse>(API_ENDPOINTS.discoverProgram, { method: "GET" }, true);
}

export async function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>(API_ENDPOINTS.stats, { method: "GET" }, true);
}

export async function getReport(scanId: string, format = "json"): Promise<ReportsResponse> {
  const query = new URLSearchParams({ scan_id: scanId, format }).toString();
  return request<ReportsResponse>(`${API_ENDPOINTS.reports}?${query}`, { method: "GET" }, true);
}

export async function downloadReportMarkdown(scanId: string): Promise<{ blob: Blob; filename: string }> {
  const token = getToken();
  if (!token) {
    throw new Error("Authentication required.");
  }
  const res = await fetch(`${API_BASE}${API_ENDPOINTS.reportsDownload(scanId)}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = (await res.json()) as { detail?: string };
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // ignore json parse errors for non-json error bodies
    }
    throw new Error(detail);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
  const filename = match?.[1] ?? `trishul-report-${scanId}.md`;
  return { blob, filename };
}

export async function getOperationsOverview(): Promise<OperationsOverviewResponse> {
  return request<OperationsOverviewResponse>(API_ENDPOINTS.operationsOverview, { method: "GET" }, true);
}

export async function getReportsAnalytics(): Promise<ReportsAnalyticsResponse> {
  return request<ReportsAnalyticsResponse>(API_ENDPOINTS.reportsAnalytics, { method: "GET" }, true);
}

export async function searchAttackedSites(query: string, limit = 20): Promise<SearchResponse> {
  const qs = new URLSearchParams({ query, limit: String(limit) }).toString();
  return request<SearchResponse>(`${API_ENDPOINTS.searchAttackedSites}?${qs}`, { method: "GET" }, true);
}

export async function recentAttackedSites(limit = 20): Promise<SearchResponse> {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return request<SearchResponse>(`${API_ENDPOINTS.searchRecent}?${qs}`, { method: "GET" }, true);
}

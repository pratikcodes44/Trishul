import type { Severity } from "@/lib/types";

export const API_ENDPOINTS = {
  register: "/api/v1/auth/register",
  login: "/api/v1/auth/login",
  startScan: "/api/v1/scans/start",
  scanStatus: (scanId: string) => `/api/v1/scans/${scanId}`,
  analyzeAsset: "/api/v1/ai/analyze-asset",
  batchAnalyze: "/api/v1/ai/batch-analyze",
  reports: "/api/v1/reports/generate",
  reportsAnalytics: "/api/v1/reports/analytics",
  operationsOverview: "/api/v1/operations/overview",
  stats: "/api/v1/stats",
  health: "/api/v1/health",
  searchAttackedSites: "/api/v1/search/attacked-sites",
  searchRecent: "/api/v1/search/recent",
} as const;

export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface StartScanRequest {
  target: string;
  scan_type: "full" | "osint" | "vulnerability" | "subdomain" | "port";
  options?: Record<string, unknown>;
}

export interface StartScanResponse {
  success: boolean;
  scan_id: string;
  target: string;
  scan_type: string;
  status: "queued" | "running" | "completed" | "failed";
  message?: string;
  estimated_time?: string;
}

export interface ScanStepStatus {
  step_id: string;
  step_name: string;
  status: "pending" | "running" | "completed" | "failed";
}

export interface ScanStatusResponse {
  scan_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  results?: {
    subdomains_found: number;
    live_hosts: number;
    open_ports: number;
    vulnerabilities: number;
  };
  completed_at?: string;
}

export interface AnalyzeAssetRequest {
  domain: string;
  technologies?: Array<{ name: string; version?: string }>;
  open_ports?: number[];
}

export interface AnalyzeAssetResponse {
  success: boolean;
  asset: string;
  analysis: {
    vulnerability_score: number;
    risk_level: string;
    exploit_likelihood: string;
    ai_analysis: string;
    reasons: string[];
  };
}

export interface FindingRecord {
  id: string;
  target: string;
  severity: Severity;
  title: string;
  context: string;
  status: "open" | "reviewed";
}

export interface ReportsResponse {
  success: boolean;
  scan_id: string;
  format: string;
  executive_summary: string;
  download_url: string;
  generated_at: string;
}

export interface StatsResponse {
  user: string;
  tier: string;
  stats: {
    total_scans: number;
    assets_monitored: number;
    vulnerabilities_found: number;
    critical_alerts: number;
    api_calls_today: number;
    storage_used_mb: number;
  };
}

export interface SearchSiteRecord {
  scan_id: string;
  target: string;
  scan_type: string;
  status: "completed" | "failed";
  progress: number;
  started_at: string;
  completed_at?: string | null;
}

export interface SearchResponse {
  success: boolean;
  query?: string;
  count: number;
  results: SearchSiteRecord[];
}

export interface OperationsOverviewResponse {
  success: boolean;
  summary: {
    total_scans: number;
    running_scans: number;
    completed_scans: number;
    failed_scans: number;
  };
  scans: Array<{
    scan_id: string;
    target: string;
    scan_type: string;
    status: string;
    progress: number;
    started_at: string;
    completed_at?: string | null;
  }>;
  events: Array<{
    scan_id?: string | null;
    event_type: string;
    detail: string;
    severity: string;
    created_at: string;
  }>;
}

export interface ReportsAnalyticsResponse {
  success: boolean;
  kpis: {
    attacked_sites: number;
    completed_scans: number;
    findings_total: number;
    risk_index: number;
  };
  recent_scans: Array<{
    scan_id: string;
    target: string;
    scan_type: string;
    status: string;
    progress: number;
    started_at: string;
    completed_at?: string | null;
  }>;
}

import type { Severity } from "@/lib/types";

export const API_ENDPOINTS = {
  register: "/api/v1/auth/register",
  login: "/api/v1/auth/login",
  startScan: "/api/v1/scans/start",
  scanStatus: (scanId: string) => `/api/v1/scans/${scanId}`,
  stopScan: (scanId: string) => `/api/v1/scans/${scanId}/stop`,
  pauseScan: (scanId: string) => `/api/v1/scans/${scanId}/pause`,
  resumeScan: (scanId: string) => `/api/v1/scans/${scanId}/resume`,
  discoverProgram: "/api/v1/programs/discover",
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
  scan_mode?: "auto" | "manual_override";
  program_url?: string;
  platform?: string;
  options?: {
    reattack_mode?: "full_rescan" | "incremental";
    partial_report_on_interrupt?: boolean;
  };
}

export interface StartScanResponse {
  success: boolean;
  scan_id: string;
  target: string;
  scan_type: string;
  scan_mode?: "auto" | "manual_override";
  reattack_mode?: "full_rescan" | "incremental";
  program_url?: string | null;
  platform?: string | null;
  status: "queued" | "running" | "paused" | "completed" | "failed" | "cancelled";
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
  status: "queued" | "running" | "paused" | "completed" | "failed" | "cancelled";
  progress: number;
  scan_mode?: "auto" | "manual_override";
  program_url?: string | null;
  platform?: string | null;
  current_phase?: number;
  current_phase_name?: string;
  current_tool?: string;
  activity_message?: string;
  activity_data?: Record<string, unknown>;
  module_insight?: string;
  error_message?: string;
  runtime_pid?: number | null;
  results?: {
    subdomains_found: number;
    live_hosts: number;
    open_ports: number;
    vulnerabilities: number;
  };
  completed_at?: string;
  updated_at?: string;
}

export interface StopScanResponse {
  success: boolean;
  scan_id: string;
  status: "cancelled" | "completed" | "failed";
  pid?: number | null;
  message?: string;
}

export interface PauseResumeScanResponse {
  success: boolean;
  scan_id: string;
  status: "paused" | "running";
  pid?: number | null;
  message?: string;
}

export interface ProgramDiscoveryResponse {
  success: boolean;
  target: string;
  program_url: string;
  platform: string;
  message?: string;
  discovered_at?: string;
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
  status: "completed" | "failed" | "cancelled";
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
    cancelled_scans?: number;
  };
  scans: Array<{
    scan_id: string;
    target: string;
    scan_type: string;
    scan_mode?: "auto" | "manual_override";
    program_url?: string | null;
    platform?: string | null;
    status: "queued" | "running" | "paused" | "completed" | "failed" | "cancelled";
    progress: number;
    current_phase?: number;
    current_phase_name?: string;
    current_tool?: string;
    activity_message?: string;
    activity_data?: Record<string, unknown>;
    module_insight?: string;
    error_message?: string;
    started_at: string;
    completed_at?: string | null;
    updated_at?: string;
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

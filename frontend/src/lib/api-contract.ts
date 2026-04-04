import type { Severity } from "@/lib/types";

export const API_ENDPOINTS = {
  startScan: "/api/v1/scans/start",
  scanStatus: (scanId: string) => `/api/v1/scans/${scanId}`,
  analyzeAsset: "/api/v1/ai/analyze-asset",
  batchAnalyze: "/api/v1/ai/batch-analyze",
  reports: "/api/v1/reports/generate",
} as const;

export interface StartScanRequest {
  target: string;
  attackType: "osint" | "crawl" | "nuclei";
}

export interface StartScanResponse {
  scan_id: string;
  status: "queued" | "running" | "completed" | "failed";
}

export interface ScanStepStatus {
  step_id: string;
  step_name: string;
  status: "pending" | "running" | "completed" | "failed";
}

export interface ScanStatusResponse {
  scan_id: string;
  target: string;
  elapsed_seconds: number;
  progress_percent: number;
  current_step: string;
  steps: ScanStepStatus[];
}

export interface AnalyzeAssetRequest {
  domain: string;
  technologies?: Array<{ name: string; version?: string }>;
  open_ports?: number[];
}

export interface AnalyzeAssetResponse {
  domain: string;
  success_confidence: number;
  risk_index: number;
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
  kpis: {
    pre_attack_success_confidence: number;
    live_attack_progress: number;
    findings_velocity: number;
    current_risk_index: number;
  };
  findings: FindingRecord[];
}

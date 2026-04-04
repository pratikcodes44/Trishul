export type AppPage = "landing" | "operations" | "reports" | "auth";

export type Severity = "critical" | "high" | "medium" | "low";

export interface CapabilityItem {
  id: string;
  title: string;
  description: string;
}

export interface WorkflowCardItem {
  id: string;
  title: string;
  description: string;
}

export interface AttackStep {
  id: string;
  title: string;
  description: string;
}

export interface AttackTemplate {
  id: string;
  name: string;
  steps: AttackStep[];
}

export interface LiveEvent {
  id: string;
  icon: "scan" | "progress" | "result";
  timestamp: string;
  detail: string;
}

export interface FindingItem {
  id: string;
  severity: Severity;
  title: string;
  context: string;
}

export interface ActivityLogItem {
  id: string;
  timestamp: string;
  message: string;
}

export interface ReportKpi {
  id: string;
  label: string;
  value: string;
  pattern?: "solid" | "dashed" | "dotted";
}

export interface ReportFilters {
  target: string;
  attackType: string;
  severity: "all" | Severity;
}

export interface ChartPoint {
  x: string;
  y: number;
}

export interface ReportCharts {
  riskTrend: ChartPoint[];
  severityDistribution: { label: Severity; value: number }[];
  scanVolume: ChartPoint[];
  endpointCategories: { label: string; value: number }[];
}

export interface ReportRow {
  id: string;
  target: string;
  severity: Severity;
  finding: string;
  status: "open" | "reviewed";
}

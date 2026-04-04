import type {
  ActivityLogItem,
  AttackTemplate,
  CapabilityItem,
  FindingItem,
  LiveEvent,
  ReportCharts,
  ReportKpi,
  ReportRow,
  WorkflowCardItem,
} from "@/lib/types";

export const capabilityItems: CapabilityItem[] = [
  { id: "recon", title: "Recon", description: "Map active subdomains and exposed surfaces." },
  { id: "osint", title: "OSINT", description: "Collect public intelligence on target footprint." },
  { id: "crawl", title: "Crawl", description: "Traverse reachable paths and linked endpoints." },
  { id: "endpoint-discovery", title: "Endpoint Discovery", description: "Identify API and hidden routes at scale." },
  { id: "risk-scoring", title: "Risk Scoring", description: "Prioritize findings by practical impact." },
  { id: "vuln-detection", title: "Vulnerability Detection", description: "Detect high-signal weaknesses automatically." },
  { id: "reporting", title: "Reporting", description: "Generate structured reports for action." },
  { id: "notifications", title: "Notifications", description: "Broadcast critical events in real time." },
];

export const workflowCards: WorkflowCardItem[] = [
  { id: "surface", title: "Surface", description: "Establish the real attack surface before execution begins." },
  { id: "analyze", title: "Analyze", description: "Apply prioritized checks using adaptive attack workflows." },
  { id: "action", title: "Action", description: "Convert validated results into decisions and remediation." },
];

export const attackTemplates: AttackTemplate[] = [
  {
    id: "osint",
    name: "OSINT Sweep",
    steps: [
      { id: "asset-profile", title: "Asset Profile", description: "Collect ownership and exposure metadata." },
      { id: "external-signals", title: "External Signals", description: "Aggregate public references and leaks." },
      { id: "validate", title: "Validate Signals", description: "Score confidence and remove weak indicators." },
    ],
  },
  {
    id: "crawl",
    name: "Web Crawl",
    steps: [
      { id: "seed", title: "Seed Paths", description: "Establish starting routes and scope boundaries." },
      { id: "traverse", title: "Traverse", description: "Expand route graph and collect endpoint metadata." },
      { id: "dedupe", title: "Deduplicate", description: "Normalize and merge endpoint variants." },
      { id: "risk-tag", title: "Risk Tagging", description: "Tag endpoints by exploitability patterns." },
      { id: "summary", title: "Summary", description: "Produce crawl summary for downstream checks." },
    ],
  },
  {
    id: "nuclei",
    name: "Nuclei Scan",
    steps: [
      { id: "template-select", title: "Template Select", description: "Select relevant template sets." },
      { id: "preflight", title: "Preflight", description: "Validate target readiness and limits." },
      { id: "execute", title: "Execute", description: "Run template batches against scoped targets." },
      { id: "verify", title: "Verify", description: "Filter noise and verify finding confidence." },
    ],
  },
];

export const liveEvents: LiveEvent[] = [
  { id: "e1", icon: "scan", timestamp: "10:42:12", detail: "Scope validation completed for target." },
  { id: "e2", icon: "progress", timestamp: "10:42:39", detail: "Endpoint discovery reached 62% coverage." },
  { id: "e3", icon: "result", timestamp: "10:43:08", detail: "Potential high-impact finding requires review." },
];

export const findings: FindingItem[] = [
  { id: "f1", severity: "high", title: "Admin endpoint exposure", context: "Unauthenticated route path discovered." },
  { id: "f2", severity: "medium", title: "Rate-limit inconsistency", context: "Burst controls vary across API nodes." },
  { id: "f3", severity: "low", title: "Header policy gap", context: "Security header set missing for static assets." },
];

export const activityLog: ActivityLogItem[] = [
  { id: "a1", timestamp: "10:41:31", message: "Execution context initialized." },
  { id: "a2", timestamp: "10:42:02", message: "Attack template selected: Nuclei Scan." },
  { id: "a3", timestamp: "10:42:57", message: "Verification stage entered for active findings." },
];

export const reportKpis: ReportKpi[] = [
  { id: "k1", label: "Pre-Attack Success Confidence", value: "78%", pattern: "solid" },
  { id: "k2", label: "Live Attack Progress", value: "43%", pattern: "dashed" },
  { id: "k3", label: "Findings Velocity", value: "1.7/min", pattern: "dotted" },
  { id: "k4", label: "Current Risk Index", value: "64", pattern: "solid" },
];

export const reportCharts: ReportCharts = {
  riskTrend: [
    { x: "09:00", y: 38 },
    { x: "10:00", y: 46 },
    { x: "11:00", y: 57 },
    { x: "12:00", y: 64 },
  ],
  severityDistribution: [
    { label: "critical", value: 2 },
    { label: "high", value: 5 },
    { label: "medium", value: 9 },
    { label: "low", value: 6 },
  ],
  scanVolume: [
    { x: "09:00", y: 60 },
    { x: "10:00", y: 95 },
    { x: "11:00", y: 132 },
    { x: "12:00", y: 110 },
  ],
  endpointCategories: [
    { label: "Auth", value: 18 },
    { label: "Admin", value: 10 },
    { label: "Data", value: 24 },
    { label: "Misc", value: 8 },
  ],
};

export const reportRows: ReportRow[] = [
  { id: "r1", target: "app.example.com", severity: "high", finding: "Access control bypass pattern", status: "open" },
  { id: "r2", target: "api.example.com", severity: "medium", finding: "Input validation weakness", status: "open" },
  { id: "r3", target: "admin.example.com", severity: "critical", finding: "Sensitive endpoint exposure", status: "open" },
  { id: "r4", target: "staging.example.com", severity: "low", finding: "Informational leakage", status: "reviewed" },
];

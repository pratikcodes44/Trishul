"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Radar, ScrollText, ShieldAlert } from "lucide-react";
import type { Severity } from "@/lib/types";
import { discoverProgram, getOperationsOverview, getScanStatus, pauseScan, resumeScan, startScan, stopScan } from "@/lib/api-client";
import { isAuthenticated } from "@/lib/auth";
import type { OperationsOverviewResponse } from "@/lib/api-contract";

function severityClass(severity: Severity) {
  switch (severity) {
    case "critical":
      return "border-[#1d1d1f] bg-[#1d1d1f] text-white";
    case "high":
      return "border-[#1d1d1f] bg-[#303035] text-white";
    case "medium":
      return "border-[#1d1d1f] bg-[#57575c] text-white";
    case "low":
      return "border-[#1d1d1f] bg-[#7a7a80] text-white";
  }
}

function moduleObjective(phaseName: string, toolName: string) {
  const phase = phaseName.toLowerCase();
  const tool = toolName.toLowerCase();
  if (tool.includes("nuclei") || phase.includes("vulnerability")) {
    return "Execute vulnerability templates against scoped targets and validate live findings.";
  }
  if (tool.includes("katana") || tool.includes("web-discovery") || tool.includes("param-discovery") || phase.includes("crawling")) {
    return "Expand endpoint coverage and surface hidden routes for deeper security testing.";
  }
  if (tool.includes("graphql") || phase.includes("graphql")) {
    return "Probe API and GraphQL endpoints for exposure, weak auth, and unsafe schema behavior.";
  }
  if (tool.includes("idor") || phase.includes("idor")) {
    return "Validate object-level authorization boundaries across discovered parameterized resources.";
  }
  if (phase.includes("subdomain")) {
    return "Discover and validate attack surface hostnames before active exploitation checks.";
  }
  if (phase.includes("port")) {
    return "Identify reachable services and prioritize high-risk exposed network surfaces.";
  }
  if (phase.includes("historical")) {
    return "Mine historical URL intelligence and test whether legacy routes remain reachable.";
  }
  return "Run the active module with controlled telemetry and continuous safety-aware progression.";
}

export function OperationsPage() {
  const [target, setTarget] = useState("app.example.com");
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState("00:00:00");
  const [scanId, setScanId] = useState("");
  const [status, setStatus] = useState<"idle" | "queued" | "running" | "paused" | "completed" | "failed" | "cancelled">("idle");
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [overview, setOverview] = useState<OperationsOverviewResponse | null>(null);
  const [mode, setMode] = useState<"auto" | "manual_override">("manual_override");
  const [reattackMode, setReattackMode] = useState<"full_rescan" | "incremental">("full_rescan");
  const [phaseName, setPhaseName] = useState("Waiting");
  const [toolName, setToolName] = useState("bootstrap");
  const [activityMessage, setActivityMessage] = useState("Waiting for activity");
  const [activityData, setActivityData] = useState<Record<string, unknown>>({});
  const [moduleInsight, setModuleInsight] = useState("Module telemetry will appear when scan execution starts.");
  const [programUrl, setProgramUrl] = useState("");
  const [platform, setPlatform] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [confirmAuto, setConfirmAuto] = useState(false);
  const [selectedHistoryTarget, setSelectedHistoryTarget] = useState("");
  const [moduleSignalAt, setModuleSignalAt] = useState(Date.now());
  const [moduleHealthTick, setModuleHealthTick] = useState(Date.now());
  const moduleSignalFingerprintRef = useRef("");

  useEffect(() => {
    if (!scanId || (status !== "running" && status !== "queued" && status !== "paused")) return;
    const timer = setInterval(async () => {
      try {
        const res = await getScanStatus(scanId);
        setProgress(res.progress ?? 0);
        setStatus(res.status);
        setPhaseName(res.current_phase_name ?? "Running");
        setToolName(res.current_tool ?? "pipeline");
        setActivityMessage(res.activity_message ?? `${res.current_phase_name ?? "Scan"} in progress`);
        setActivityData(res.activity_data ?? {});
        setModuleInsight(res.module_insight ?? "Module is processing current phase workload.");
        if (res.program_url) setProgramUrl(res.program_url);
        if (res.platform) setPlatform(res.platform);
        if (res.error_message) setError(res.error_message);
        if (res.status === "completed" || res.status === "failed" || res.status === "cancelled") {
          setRunning(false);
          clearInterval(timer);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch scan status");
        setRunning(false);
        clearInterval(timer);
      }
    }, 1200);
    return () => clearInterval(timer);
  }, [scanId, status]);

  useEffect(() => {
    if (!running || status === "paused") return;
    const started = Date.now();
    const timer = setInterval(() => {
      const diff = Math.floor((Date.now() - started) / 1000);
      const hh = String(Math.floor(diff / 3600)).padStart(2, "0");
      const mm = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
      const ss = String(diff % 60).padStart(2, "0");
      setElapsed(`${hh}:${mm}:${ss}`);
    }, 1000);
    return () => clearInterval(timer);
  }, [running, status]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    getOperationsOverview().then(setOverview).catch(() => undefined);
  }, [status, scanId]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    const runningScan = (overview?.scans ?? []).find(
      (item) => item.status === "running" || item.status === "queued" || item.status === "paused",
    );
    if (!runningScan || scanId) return;
    setScanId(runningScan.scan_id);
    setTarget(runningScan.target);
    setMode((runningScan.scan_mode as "auto" | "manual_override") ?? "manual_override");
    setStatus(runningScan.status);
    setRunning(runningScan.status === "running" || runningScan.status === "queued" || runningScan.status === "paused");
    setProgress(runningScan.progress ?? 0);
    setPhaseName(runningScan.current_phase_name || "Initializing");
    setToolName(runningScan.current_tool || "pipeline");
    setActivityMessage(runningScan.activity_message || `${runningScan.current_phase_name || "Scan"} in progress`);
    setActivityData((runningScan.activity_data as Record<string, unknown> | undefined) ?? {});
    setModuleInsight(runningScan.module_insight || "Module is processing current phase workload.");
    setProgramUrl(runningScan.program_url ?? "");
    setPlatform(runningScan.platform ?? "");
  }, [overview, scanId]);

  useEffect(() => {
    if (!isAuthenticated() || (!running && !scanId)) return;
    const timer = setInterval(() => {
      getOperationsOverview().then(setOverview).catch(() => undefined);
    }, 1800);
    return () => clearInterval(timer);
  }, [running, scanId]);

  useEffect(() => {
    const match = (overview?.scans ?? []).find((item) => item.scan_id === scanId);
    if (!match) return;
    setProgress(match.progress ?? 0);
    setStatus(match.status);
    if (match.current_phase_name) setPhaseName(match.current_phase_name);
    if (match.current_tool) setToolName(match.current_tool);
    if (match.activity_message) setActivityMessage(match.activity_message);
    setActivityData((match.activity_data as Record<string, unknown> | undefined) ?? {});
    if (match.module_insight) setModuleInsight(match.module_insight);
    if (match.program_url) setProgramUrl(match.program_url);
    if (match.platform) setPlatform(match.platform);
    if (match.status === "completed" || match.status === "failed" || match.status === "cancelled") {
      setRunning(false);
    } else {
      setRunning(true);
    }
  }, [overview, scanId]);

  const websiteHistory = useMemo(() => {
    const scans = overview?.scans ?? [];
    const grouped = new Map<string, typeof scans>();
    for (const item of scans) {
      const existing = grouped.get(item.target) ?? [];
      existing.push(item);
      grouped.set(item.target, existing);
    }
    return Array.from(grouped.entries())
      .map(([site, entries]) => ({
        site,
        scans: entries.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()),
      }))
      .sort((a, b) => {
        const aTime = a.scans[0] ? new Date(a.scans[0].started_at).getTime() : 0;
        const bTime = b.scans[0] ? new Date(b.scans[0].started_at).getTime() : 0;
        return bTime - aTime;
      });
  }, [overview]);

  useEffect(() => {
    if (!selectedHistoryTarget && websiteHistory.length > 0) {
      setSelectedHistoryTarget(websiteHistory[0].site);
    }
    if (selectedHistoryTarget && !websiteHistory.some((item) => item.site === selectedHistoryTarget)) {
      setSelectedHistoryTarget(websiteHistory[0]?.site ?? "");
    }
  }, [websiteHistory, selectedHistoryTarget]);

  const selectedHistoryScans = useMemo(() => {
    const targetGroup = websiteHistory.find((item) => item.site === selectedHistoryTarget);
    return targetGroup?.scans ?? [];
  }, [websiteHistory, selectedHistoryTarget]);

  useEffect(() => {
    if (!scanId) {
      moduleSignalFingerprintRef.current = "";
      setModuleSignalAt(Date.now());
      return;
    }
    const signalPayload = {
      toolName,
      activityMessage,
      status,
      activeUrlSample: typeof activityData.active_url_sample === "string" ? activityData.active_url_sample : "",
      activeUrl: typeof activityData.active_url === "string" ? activityData.active_url : "",
      requestsSent: typeof activityData.requests_sent === "number" ? activityData.requests_sent : null,
      requestsTotal: typeof activityData.requests_total === "number" ? activityData.requests_total : null,
      findingsCount: typeof activityData.findings_count === "number" ? activityData.findings_count : null,
      currentTemplate: typeof activityData.current_template === "string" ? activityData.current_template : "",
      currentIndex: typeof activityData.current_index === "number" ? activityData.current_index : null,
      totalUrls: typeof activityData.total_urls === "number" ? activityData.total_urls : null,
      urlsDiscovered: typeof activityData.urls_discovered === "number" ? activityData.urls_discovered : null,
    };
    const nextFingerprint = JSON.stringify(signalPayload);
    if (nextFingerprint !== moduleSignalFingerprintRef.current) {
      moduleSignalFingerprintRef.current = nextFingerprint;
      setModuleSignalAt(Date.now());
    }
  }, [activityData, activityMessage, scanId, status, toolName]);

  useEffect(() => {
    if (!scanId || (status !== "running" && status !== "queued")) return;
    const timer = setInterval(() => setModuleHealthTick(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [scanId, status]);

  const attackStatisticsRows = useMemo(() => {
    const rows: Array<{ label: string; value: string }> = [];
    rows.push({ label: "Module in focus", value: toolName || "N/A" });
    rows.push({ label: "Module objective", value: moduleObjective(phaseName, toolName) });
    rows.push({ label: "Current module operation", value: activityMessage || "Running module workflow." });
    rows.push({ label: "AI module readout", value: moduleInsight });
    const requestsSent = typeof activityData.requests_sent === "number" ? activityData.requests_sent : null;
    const requestsTotal = typeof activityData.requests_total === "number" ? activityData.requests_total : null;
    const currentIndex = typeof activityData.current_index === "number" ? activityData.current_index : null;
    const totalUrls = typeof activityData.total_urls === "number" ? activityData.total_urls : null;
    const urlsDiscovered = typeof activityData.urls_discovered === "number" ? activityData.urls_discovered : null;
    const chunkMode = typeof activityData.chunk_mode === "string" ? activityData.chunk_mode : "";
    const totalChunks = typeof activityData.total_chunks === "number" ? activityData.total_chunks : null;
    const completedChunks = typeof activityData.completed_chunks === "number" ? activityData.completed_chunks : null;
    const activeChunks = typeof activityData.active_chunks === "number" ? activityData.active_chunks : null;
    const workers = typeof activityData.workers === "number" ? activityData.workers : null;

    const hasGranularProgress =
      (requestsSent !== null && requestsTotal !== null && requestsTotal > 0) ||
      (currentIndex !== null && totalUrls !== null && totalUrls > 0) ||
      urlsDiscovered !== null ||
      (totalChunks !== null && totalChunks > 0 && completedChunks !== null);

    const moduleProgressLabel =
      totalChunks !== null && totalChunks > 0 && completedChunks !== null
        ? `${Math.min(100, Math.round((completedChunks / totalChunks) * 100))}% (${completedChunks}/${totalChunks} chunks)`
        : requestsSent !== null && requestsTotal !== null && requestsTotal > 0
        ? `${Math.min(100, Math.round((requestsSent / requestsTotal) * 100))}% (${requestsSent}/${requestsTotal} requests)`
        : currentIndex !== null && totalUrls !== null && totalUrls > 0
          ? `${Math.min(100, Math.round((currentIndex / totalUrls) * 100))}% (${currentIndex}/${totalUrls} endpoints)`
          : urlsDiscovered !== null
            ? `${urlsDiscovered} URLs discovered (live module output)`
            : status === "completed"
              ? "100% (module finished)"
              : status === "paused"
                ? "Paused"
                : "In progress (no module percentage telemetry)";
    rows.push({ label: "Module completion", value: moduleProgressLabel });
    if (totalChunks !== null && totalChunks > 0) {
      rows.push({
        label: "Chunk scheduler",
        value: `${chunkMode || "chunked"} • active ${activeChunks ?? 0}/${totalChunks} • workers ${workers ?? 0}`,
      });
    }

    const secondsSinceSignal = Math.max(0, Math.floor((moduleHealthTick - moduleSignalAt) / 1000));
    const moduleHealthLabel =
      status === "paused"
        ? "Paused by user/runtime control"
        : status === "completed"
          ? "Completed"
          : status === "failed"
            ? "Failed"
            : status === "cancelled"
              ? "Cancelled"
              : hasGranularProgress
                ? secondsSinceSignal <= 20
                  ? `Working (fresh module signal ${secondsSinceSignal}s ago)`
                  : secondsSinceSignal <= 75
                    ? `Slow but active (last module signal ${secondsSinceSignal}s ago)`
                    : `Possibly stuck (no module signal for ${secondsSinceSignal}s)`
                : "Working (module has no granular telemetry; monitoring runtime state)";
    rows.push({ label: "Module activity state", value: moduleHealthLabel });

    const activeUrlSample = typeof activityData.active_url_sample === "string" ? activityData.active_url_sample : "";
    if (activeUrlSample) rows.push({ label: "Current URL sample", value: activeUrlSample });

    const activeApiUrl = typeof activityData.active_url === "string" ? activityData.active_url : "";
    if (activeApiUrl) rows.push({ label: "Current endpoint", value: activeApiUrl });

    if (requestsSent !== null || requestsTotal !== null) {
      rows.push({ label: "Nuclei requests", value: `${requestsSent ?? 0}/${requestsTotal ?? 0}` });
    }

    const findingsCount = typeof activityData.findings_count === "number" ? activityData.findings_count : null;
    if (findingsCount !== null) rows.push({ label: "Live findings", value: String(findingsCount) });

    const currentTemplate = typeof activityData.current_template === "string" ? activityData.current_template : "";
    if (currentTemplate) rows.push({ label: "Current template", value: currentTemplate });

    const rps = typeof activityData.rps === "number" ? activityData.rps : null;
    if (rps !== null) rows.push({ label: "Requests/sec", value: String(rps) });

    const etaSeconds = typeof activityData.eta_seconds === "number" ? activityData.eta_seconds : null;
    if (etaSeconds !== null) rows.push({ label: "ETA (sec)", value: String(etaSeconds) });

    const hostsTotal = typeof activityData.hosts_total === "number" ? activityData.hosts_total : null;
    if (hostsTotal !== null) rows.push({ label: "Hosts in crawl", value: String(hostsTotal) });

    if (urlsDiscovered !== null) rows.push({ label: "URLs discovered", value: String(urlsDiscovered) });

    const totalTargets = typeof activityData.total_targets === "number" ? activityData.total_targets : null;
    if (totalTargets !== null) rows.push({ label: "Nuclei target set", value: String(totalTargets) });

    if (currentIndex !== null && totalUrls !== null) {
      rows.push({ label: "GraphQL progress", value: `${currentIndex}/${totalUrls}` });
    }

    return rows;
  }, [activityData, activityMessage, moduleHealthTick, moduleInsight, moduleSignalAt, phaseName, status, toolName]);

  async function handleManualStart() {
    if (!isAuthenticated()) {
      setError("Please sign in at /auth before starting a scan.");
      return;
    }
    if (!target.trim()) {
      setError("Please provide a target.");
      return;
    }
    setError(null);
    setRunning(true);
    setStatus("queued");
    try {
      const res = await startScan({
        target: target.trim(),
        scan_type: "full",
        scan_mode: "manual_override",
        program_url: "N/A (Manual Override)",
        platform: "Manual Override",
        options: {
          reattack_mode: reattackMode,
          partial_report_on_interrupt: true,
        },
      });
      setScanId(res.scan_id);
      setStatus(res.status);
      setReattackMode(res.reattack_mode ?? reattackMode);
      setProgramUrl(res.program_url ?? "");
      setPlatform(res.platform ?? "");
      setPhaseName("Initializing");
      setToolName("bootstrap");
      setActivityMessage("Manual scan queued in backend runtime");
      setActivityData({});
      setModuleInsight("Module insight activates when runtime telemetry starts streaming.");
    } catch (err) {
      setRunning(false);
      setStatus("failed");
      setError(err instanceof Error ? err.message : "Failed to start scan");
    }
  }

  async function handleAutoDiscover() {
    if (!isAuthenticated()) {
      setError("Please sign in at /auth before starting a scan.");
      return;
    }
    setError(null);
    setConfirmAuto(false);
    setDiscovering(true);
    try {
      const discovered = await discoverProgram();
      setTarget(discovered.target);
      setProgramUrl(discovered.program_url);
      setPlatform(discovered.platform);
      setConfirmAuto(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discover bug bounty program");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleAutoStartConfirmed() {
    if (!target.trim()) {
      setError("No discovered target available.");
      return;
    }
    setError(null);
    setConfirmAuto(false);
    setRunning(true);
    setStatus("queued");
    try {
      const res = await startScan({
        target: target.trim(),
        scan_type: "full",
        scan_mode: "auto",
        program_url: programUrl,
        platform,
        options: {
          reattack_mode: reattackMode,
          partial_report_on_interrupt: true,
        },
      });
      setScanId(res.scan_id);
      setStatus(res.status);
      setReattackMode(res.reattack_mode ?? reattackMode);
      setPhaseName("Initializing");
      setToolName("bootstrap");
      setActivityMessage("Auto scan queued in backend runtime");
      setActivityData({});
      setModuleInsight("Module insight activates when runtime telemetry starts streaming.");
    } catch (err) {
      setRunning(false);
      setStatus("failed");
      setError(err instanceof Error ? err.message : "Failed to start auto scan");
    }
  }

  async function handleStopScan() {
    if (!scanId) return;
    setError(null);
    try {
      const res = await stopScan(scanId);
      setStatus(res.status);
      setRunning(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop scan");
    }
  }

  async function handlePauseScan() {
    if (!scanId) return;
    setError(null);
    try {
      const res = await pauseScan(scanId);
      setStatus(res.status);
      setRunning(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to pause scan");
    }
  }

  async function handleResumeScan() {
    if (!scanId) return;
    setError(null);
    try {
      const res = await resumeScan(scanId);
      setStatus(res.status);
      setRunning(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resume scan");
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 pb-10 pt-6 sm:px-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="space-y-6">
          <article className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[#1d1d1f]">Workflow Wizard</h2>
            <p className="mt-1 text-sm text-[#6e6e73]">
              Choose mode. Auto discovers HackerOne/Bugcrowd programs; Manual Override starts directly on your target.
            </p>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <label className="text-sm">
                <span className="mb-1 block text-[#6e6e73]">Workflow Mode</span>
                <select
                  value={mode}
                  onChange={(e) => {
                    const next = e.target.value as "auto" | "manual_override";
                    setMode(next);
                    setConfirmAuto(false);
                    setError(null);
                    if (next === "manual_override") {
                      setProgramUrl("");
                      setPlatform("");
                    }
                  }}
                  className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                >
                  <option value="auto">Auto</option>
                  <option value="manual_override">Manual Override</option>
                </select>
              </label>

              <label className="text-sm">
                <span className="mb-1 block text-[#6e6e73]">Target</span>
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  disabled={mode === "auto"}
                  placeholder={mode === "auto" ? "Auto-discovered target appears here" : "example.com"}
                  className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                />
              </label>

              <label className="text-sm">
                <span className="mb-1 block text-[#6e6e73]">Re-attack Strategy</span>
                <select
                  value={reattackMode}
                  onChange={(e) => setReattackMode(e.target.value as "full_rescan" | "incremental")}
                  disabled={running}
                  className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                >
                  <option value="full_rescan">Full re-attack (recommended)</option>
                  <option value="incremental">Incremental (new assets only)</option>
                </select>
              </label>
            </div>
            <div className="mt-4 flex items-center gap-3">
              {mode === "manual_override" ? (
                <button
                  className="h-10 rounded-xl bg-[#1d1d1f] px-4 text-sm font-medium text-white disabled:opacity-60"
                  type="button"
                  onClick={handleManualStart}
                  disabled={running}
                >
                  {running ? "Running..." : "Start scan"}
                </button>
              ) : (
                <button
                  className="h-10 rounded-xl bg-[#1d1d1f] px-4 text-sm font-medium text-white disabled:opacity-60"
                  type="button"
                  onClick={handleAutoDiscover}
                  disabled={running || discovering}
                >
                  {discovering ? "Discovering..." : "Start scan"}
                </button>
              )}
              <button
                className="h-10 rounded-xl border border-[#d2d2d7] bg-white px-4 text-sm font-medium text-[#1d1d1f] disabled:opacity-50"
                type="button"
                onClick={handlePauseScan}
                disabled={!scanId || status !== "running"}
              >
                Pause
              </button>
              <button
                className="h-10 rounded-xl border border-[#d2d2d7] bg-white px-4 text-sm font-medium text-[#1d1d1f] disabled:opacity-50"
                type="button"
                onClick={handleResumeScan}
                disabled={!scanId || status !== "paused"}
              >
                Resume
              </button>
              <button
                className="h-10 rounded-xl border border-[#d2d2d7] bg-white px-4 text-sm font-medium text-[#1d1d1f] disabled:opacity-50"
                type="button"
                onClick={handleStopScan}
                disabled={!scanId || (status !== "running" && status !== "paused" && status !== "queued")}
              >
                Stop
              </button>
              <span className="text-xs text-[#6e6e73]">Status: {status}</span>
              {overview ? (
                <span className="text-xs text-[#6e6e73]">
                  Completed: {overview.summary.completed_scans} • Running: {overview.summary.running_scans}
                </span>
              ) : null}
            </div>
            {confirmAuto ? (
              <div className="mt-3 rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3 text-sm text-[#1d1d1f]">
                <p>
                  Found {platform || "program"} target <span className="font-medium">{target}</span>.
                </p>
                {programUrl ? (
                  <p className="mt-1 text-xs text-[#6e6e73]">
                    Official program: <span className="break-all">{programUrl}</span>
                  </p>
                ) : null}
                <div className="mt-3 flex items-center gap-2">
                  <button
                    className="h-9 rounded-xl bg-[#1d1d1f] px-3 text-sm font-medium text-white"
                    type="button"
                    onClick={handleAutoStartConfirmed}
                  >
                    Yes, start
                  </button>
                  <button
                    className="h-9 rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm font-medium text-[#1d1d1f]"
                    type="button"
                    onClick={() => setConfirmAuto(false)}
                  >
                    No
                  </button>
                </div>
              </div>
            ) : null}
            {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}

            <div className="mt-4 space-y-2">
              <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] px-3 py-2">
                <p className="text-sm font-medium text-[#1d1d1f]">Runtime Pipeline</p>
                <p className="text-xs text-[#6e6e73]">
                  Backend executes the real phases and updates this dashboard live.
                </p>
              </div>
              <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] px-3 py-2">
                <p className="text-sm font-medium text-[#1d1d1f]">Current phase</p>
                <p className="text-xs text-[#6e6e73]">{phaseName}</p>
              </div>
              <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] px-3 py-2">
                <p className="text-sm font-medium text-[#1d1d1f]">Current tool</p>
                <p className="text-xs text-[#6e6e73]">{toolName}</p>
              </div>
              <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] px-3 py-2">
                <p className="text-sm font-medium text-[#1d1d1f]">Current scan ID</p>
                <p className="break-all font-mono text-xs text-[#6e6e73]">{scanId || "Not started"}</p>
              </div>
            </div>
          </article>

          <article className="surface-card p-5">
            <h3 className="text-base font-semibold text-[#1d1d1f]">Attack Progress</h3>
            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-[#6e6e73]">Progress</span>
                <span className="font-medium text-[#1d1d1f]">{progress}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-[#e5e5ea]">
                <div className="h-2 rounded-full bg-[#1d1d1f]" style={{ width: `${progress}%` }} />
              </div>
            </div>
            <div className="mt-3 text-sm">
              <span className="text-[#6e6e73]">Elapsed Time: </span>
              <span className="font-medium text-[#1d1d1f]">{elapsed}</span>
            </div>
          </article>

          <article className="surface-card p-5">
            <h3 className="text-base font-semibold text-[#1d1d1f]">Attack Details</h3>
            <dl className="mt-3 grid grid-cols-1 gap-2 text-sm">
              <div>
                <dt className="text-[#6e6e73]">Current Step</dt>
                <dd className="font-medium text-[#1d1d1f]">{phaseName}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Target</dt>
                <dd className="font-medium text-[#1d1d1f]">{target}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Tool/Module</dt>
                <dd className="font-medium text-[#1d1d1f]">{toolName}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Mode</dt>
                <dd className="font-medium text-[#1d1d1f]">{mode === "auto" ? "Auto" : "Manual Override"}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Re-attack policy</dt>
                <dd className="font-medium text-[#1d1d1f]">
                  {reattackMode === "full_rescan" ? "Full re-attack on repeat targets" : "Incremental (new discoveries only)"}
                </dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Status</dt>
                <dd className="font-medium text-[#1d1d1f]">
                  {status === "running"
                    ? "Actively analyzing current execution surface."
                    : status === "paused"
                      ? "Pipeline is paused. Resume to continue from current phase."
                      : `Current state: ${status}`}
                </dd>
              </div>
              {programUrl ? (
                <div>
                  <dt className="text-[#6e6e73]">Program URL</dt>
                  <dd className="break-all font-medium text-[#1d1d1f]">{programUrl}</dd>
                </div>
              ) : null}
            </dl>
          </article>

          <article className="surface-card p-5">
            <h3 className="text-base font-semibold text-[#1d1d1f]">Website History</h3>
            {websiteHistory.length === 0 ? (
              <p className="mt-3 text-sm text-[#6e6e73]">No website history yet.</p>
            ) : (
              <div className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-[200px_minmax(0,1fr)]">
                <div className="space-y-2">
                  {websiteHistory.map((item) => (
                    <button
                      key={item.site}
                      type="button"
                      onClick={() => setSelectedHistoryTarget(item.site)}
                      className={`w-full rounded-xl border px-3 py-2 text-left text-sm ${
                        selectedHistoryTarget === item.site
                          ? "border-[#1d1d1f] bg-[#1d1d1f] text-white"
                          : "border-[#d2d2d7] bg-white text-[#1d1d1f]"
                      }`}
                    >
                      <p className="truncate font-medium">{item.site}</p>
                      <p className={`text-xs ${selectedHistoryTarget === item.site ? "text-[#f5f5f7]" : "text-[#6e6e73]"}`}>
                        {item.scans.length} scan{item.scans.length > 1 ? "s" : ""}
                      </p>
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  {selectedHistoryScans.length === 0 ? (
                    <p className="text-sm text-[#6e6e73]">Select a website to view details.</p>
                  ) : (
                    selectedHistoryScans.slice(0, 8).map((entry) => (
                      <div key={entry.scan_id} className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                        <p className="text-sm font-medium text-[#1d1d1f]">{entry.target}</p>
                        <p className="mt-1 break-all font-mono text-xs text-[#6e6e73]">Scan ID: {entry.scan_id}</p>
                        <p className="mt-1 text-xs text-[#6e6e73]">
                          Previous completion: {entry.progress}% • {entry.status}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </article>
        </section>

        <section className="space-y-6">
          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Radar className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Attack Statistics</h3>
            </div>
            <div className="max-h-[240px] space-y-2 overflow-y-auto pr-1">
              {attackStatisticsRows.map((row) => (
                <div key={row.label} className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <p className="text-xs text-[#6e6e73]">{row.label}</p>
                  <p className="mt-1 break-all text-sm font-medium text-[#1d1d1f]">{row.value}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Radar className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Live Status Stream</h3>
            </div>
            <div className="max-h-[240px] space-y-3 overflow-y-auto pr-1">
              {(overview?.events ?? []).map((event) => (
                <div key={`${event.scan_id ?? "evt"}-${event.created_at}`} className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <div className="mb-1 flex items-center gap-2 text-xs text-[#6e6e73]">
                    <span>{new Date(event.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-sm text-[#1d1d1f]">{event.detail}</p>
                </div>
              ))}
              {overview && overview.events.length === 0 ? (
                <p className="text-sm text-[#6e6e73]">No activity events yet.</p>
              ) : null}
            </div>
          </article>

          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Findings</h3>
            </div>
            <div className="max-h-[240px] space-y-2 overflow-y-auto pr-1">
              {(overview?.scans ?? []).slice(0, 4).map((item) => (
                <div key={item.scan_id} className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={`inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase ${severityClass(
                        item.status === "failed" ? "high" : item.status === "completed" ? "low" : item.status === "cancelled" ? "high" : "medium",
                      )}`}
                    >
                      {item.status}
                    </span>
                    <span className="text-sm font-medium text-[#1d1d1f]">{item.target}</span>
                  </div>
                  <p className="text-sm text-[#6e6e73]">
                    {item.scan_type} • {item.progress}% • {item.current_phase_name || "Pending"} • {item.scan_id.slice(0, 8)}
                  </p>
                </div>
              ))}
              {overview && overview.scans.length === 0 ? (
                <p className="text-sm text-[#6e6e73]">No scan history yet.</p>
              ) : null}
            </div>
          </article>

          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Recent Activity</h3>
            </div>
            <div className="max-h-[240px] space-y-2 overflow-y-auto pr-1">
              {(overview?.scans ?? []).slice(0, 4).map((item) => (
                <div key={`${item.scan_id}-recent`} className="flex items-start gap-3 rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <ScrollText className="mt-0.5 h-4 w-4 text-[#6e6e73]" />
                  <div>
                    <p className="text-xs text-[#6e6e73]">{new Date(item.started_at).toLocaleString()}</p>
                    <p className="text-sm text-[#1d1d1f]">
                      {item.target} • {item.status} • {item.scan_mode ?? "manual_override"}
                    </p>
                  </div>
                </div>
              ))}
              {overview && overview.scans.length === 0 ? (
                <p className="text-sm text-[#6e6e73]">No recent activity yet.</p>
              ) : null}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}

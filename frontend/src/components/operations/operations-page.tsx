"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Radar, ScrollText, ShieldAlert } from "lucide-react";
import { attackTemplates } from "@/lib/mock-data";
import type { AttackTemplate, Severity } from "@/lib/types";
import { getOperationsOverview, getScanStatus, startScan } from "@/lib/api-client";
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

export function OperationsPage() {
  const [templateId, setTemplateId] = useState(attackTemplates[0].id);
  const [target, setTarget] = useState("app.example.com");
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState("00:00:00");
  const [scanId, setScanId] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [overview, setOverview] = useState<OperationsOverviewResponse | null>(null);

  const template: AttackTemplate = useMemo(
    () => attackTemplates.find((item) => item.id === templateId) ?? attackTemplates[0],
    [templateId],
  );

  useEffect(() => {
    if (!scanId || status !== "running") return;
    const timer = setInterval(async () => {
      try {
        const res = await getScanStatus(scanId);
        setProgress(res.progress ?? 0);
        setStatus(res.status);
        if (res.status === "completed" || res.status === "failed") {
          setRunning(false);
          clearInterval(timer);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch scan status");
        setRunning(false);
        clearInterval(timer);
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [scanId, status]);

  useEffect(() => {
    if (!running) return;
    const started = Date.now();
    const timer = setInterval(() => {
      const diff = Math.floor((Date.now() - started) / 1000);
      const hh = String(Math.floor(diff / 3600)).padStart(2, "0");
      const mm = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
      const ss = String(diff % 60).padStart(2, "0");
      setElapsed(`${hh}:${mm}:${ss}`);
    }, 1000);
    return () => clearInterval(timer);
  }, [running]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    getOperationsOverview().then(setOverview).catch(() => undefined);
  }, [status, scanId]);

  async function handleStartScan() {
    if (!isAuthenticated()) {
      setError("Please sign in at /auth before starting a scan.");
      return;
    }
    setError(null);
    setRunning(true);
    setStatus("queued");
    try {
      const scanType = templateId === "nuclei" ? "vulnerability" : templateId === "crawl" ? "full" : "osint";
      const res = await startScan({ target, scan_type: scanType });
      setScanId(res.scan_id);
      setStatus(res.status);
    } catch (err) {
      setRunning(false);
      setStatus("failed");
      setError(err instanceof Error ? err.message : "Failed to start scan");
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 pb-10 pt-6 sm:px-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="space-y-6">
          <article className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[#1d1d1f]">Workflow Wizard</h2>
            <p className="mt-1 text-sm text-[#6e6e73]">
              Steps adapt based on selected attack template. Future backend wiring will replace mock templates.
            </p>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block text-[#6e6e73]">Attack Type</span>
                <select
                  value={templateId}
                  onChange={(e) => setTemplateId(e.target.value)}
                  className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                >
                  {attackTemplates.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm">
                <span className="mb-1 block text-[#6e6e73]">Target</span>
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                />
              </label>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <button
                className="h-10 rounded-xl bg-[#1d1d1f] px-4 text-sm font-medium text-white disabled:opacity-60"
                type="button"
                onClick={handleStartScan}
                disabled={running}
              >
                {running ? "Running..." : "Start scan"}
              </button>
              <span className="text-xs text-[#6e6e73]">Status: {status}</span>
              {scanId ? <span className="text-xs text-[#6e6e73]">Scan ID: {scanId}</span> : null}
              {overview ? (
                <span className="text-xs text-[#6e6e73]">
                  Completed: {overview.summary.completed_scans} • Running: {overview.summary.running_scans}
                </span>
              ) : null}
            </div>
            {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}

            <div className="mt-4 space-y-2">
              {template.steps.map((step, index) => (
                <div key={step.id} className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] px-3 py-2">
                  <p className="text-sm font-medium text-[#1d1d1f]">
                    Step {index + 1}: {step.title}
                  </p>
                  <p className="text-xs text-[#6e6e73]">{step.description}</p>
                </div>
              ))}
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
                <dd className="font-medium text-[#1d1d1f]">{template.steps[1]?.title ?? template.steps[0].title}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Target</dt>
                <dd className="font-medium text-[#1d1d1f]">{target}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Tool/Module</dt>
                <dd className="font-medium text-[#1d1d1f]">{template.name}</dd>
              </div>
              <div>
                <dt className="text-[#6e6e73]">Status</dt>
                <dd className="font-medium text-[#1d1d1f]">
                  {status === "running" ? "Actively analyzing current execution surface." : `Current state: ${status}`}
                </dd>
              </div>
            </dl>
          </article>
        </section>

        <section className="space-y-6">
          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Radar className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Live Status Stream</h3>
            </div>
            <div className="space-y-3">
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
            <div className="space-y-2">
              {(overview?.scans ?? []).slice(0, 6).map((item) => (
                <div key={item.scan_id} className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={`inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase ${severityClass(
                        item.status === "failed" ? "high" : item.status === "completed" ? "low" : "medium",
                      )}`}
                    >
                      {item.status}
                    </span>
                    <span className="text-sm font-medium text-[#1d1d1f]">{item.target}</span>
                  </div>
                  <p className="text-sm text-[#6e6e73]">
                    {item.scan_type} • {item.progress}% • {item.scan_id.slice(0, 8)}
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
            <div className="space-y-2">
              {(overview?.scans ?? []).slice(0, 6).map((item) => (
                <div key={`${item.scan_id}-recent`} className="flex items-start gap-3 rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <ScrollText className="mt-0.5 h-4 w-4 text-[#6e6e73]" />
                  <div>
                    <p className="text-xs text-[#6e6e73]">{new Date(item.started_at).toLocaleString()}</p>
                    <p className="text-sm text-[#1d1d1f]">
                      {item.target} • {item.status} • {item.scan_type}
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

"use client";

import { useMemo, useState } from "react";
import { Activity, Radar, ScrollText, ShieldAlert } from "lucide-react";
import { activityLog, attackTemplates, findings, liveEvents } from "@/lib/mock-data";
import type { AttackTemplate, Severity } from "@/lib/types";

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
  const [progress, setProgress] = useState(43);
  const [elapsed, setElapsed] = useState("00:07:18");

  const template: AttackTemplate = useMemo(
    () => attackTemplates.find((item) => item.id === templateId) ?? attackTemplates[0],
    [templateId],
  );

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
                <dd className="font-medium text-[#1d1d1f]">Actively analyzing current execution surface.</dd>
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
              {liveEvents.map((event) => (
                <div key={event.id} className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <div className="mb-1 flex items-center gap-2 text-xs text-[#6e6e73]">
                    <span>{event.timestamp}</span>
                  </div>
                  <p className="text-sm text-[#1d1d1f]">{event.detail}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Findings</h3>
            </div>
            <div className="space-y-2">
              {findings.map((item) => (
                <div key={item.id} className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <span
                      className={`inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium uppercase ${severityClass(
                        item.severity,
                      )}`}
                    >
                      {item.severity}
                    </span>
                    <span className="text-sm font-medium text-[#1d1d1f]">{item.title}</span>
                  </div>
                  <p className="text-sm text-[#6e6e73]">{item.context}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="surface-card p-5">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#1d1d1f]" />
              <h3 className="text-base font-semibold text-[#1d1d1f]">Recent Activity</h3>
            </div>
            <div className="space-y-2">
              {activityLog.map((item) => (
                <div key={item.id} className="flex items-start gap-3 rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
                  <ScrollText className="mt-0.5 h-4 w-4 text-[#6e6e73]" />
                  <div>
                    <p className="text-xs text-[#6e6e73]">{item.timestamp}</p>
                    <p className="text-sm text-[#1d1d1f]">{item.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}

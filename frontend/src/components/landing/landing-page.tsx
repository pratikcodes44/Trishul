"use client";

import { useRouter } from "next/navigation";
import { Shield, SearchCode, Radar, Network, AlertCircle, FileCheck, Bell, BrainCircuit } from "lucide-react";
import { capabilityItems, workflowCards } from "@/lib/mock-data";
import { ScrollRevealItem, ScrollRevealSection } from "@/components/ui/scroll-reveal-section";

const iconMap = [Shield, SearchCode, Radar, Network, BrainCircuit, AlertCircle, FileCheck, Bell];

export function LandingPage() {
  const router = useRouter();

  return (
    <main className="mx-auto max-w-7xl px-4 pb-16 pt-12 sm:px-6">
      <section className="surface-card mb-12 px-6 py-14 text-center sm:px-12">
        <h2 className="mx-auto max-w-3xl text-3xl font-semibold tracking-tight text-[#1d1d1f] sm:text-5xl">
          Security operations with confident visibility and premium control.
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-[#6e6e73]">
          Build a complete view of your attack surface, analyze risk with structure, and move findings into action.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            onClick={() => router.push("/auth")}
            className="h-11 rounded-xl bg-[#1d1d1f] px-5 text-sm font-medium text-white transition-colors hover:bg-[#000]"
          >
            Sign In to Start
          </button>
          <button
            onClick={() => router.push("/reports")}
            className="h-11 rounded-xl border border-[#d2d2d7] bg-white px-5 text-sm font-medium text-[#1d1d1f] transition-colors hover:bg-[#f5f5f7]"
          >
            View Reports
          </button>
        </div>
      </section>

      <section className="mb-12">
        <h3 className="mb-5 text-xl font-semibold text-[#1d1d1f]">Workflow Preview</h3>
        <ScrollRevealSection className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {workflowCards.map((card) => (
            <ScrollRevealItem key={card.id}>
              <article className="surface-card h-full p-5 shadow-[0_12px_30px_rgba(0,0,0,0.12)]">
                <h4 className="text-lg font-semibold text-[#1d1d1f]">{card.title}</h4>
                <p className="mt-2 text-sm text-[#6e6e73]">{card.description}</p>
              </article>
            </ScrollRevealItem>
          ))}
        </ScrollRevealSection>
      </section>

      <section>
        <h3 className="mb-5 text-xl font-semibold text-[#1d1d1f]">Capabilities</h3>

        <ScrollRevealSection className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {capabilityItems.slice(0, 4).map((item, idx) => {
            const Icon = iconMap[idx];
            return (
              <ScrollRevealItem key={item.id}>
                <article className="surface-card h-full p-5 shadow-[0_12px_30px_rgba(0,0,0,0.16)]">
                  <Icon className="h-5 w-5 text-[#1d1d1f]" />
                  <h4 className="mt-3 text-base font-semibold text-[#1d1d1f]">{item.title}</h4>
                  <p className="mt-1 text-sm text-[#6e6e73]">{item.description}</p>
                </article>
              </ScrollRevealItem>
            );
          })}
        </ScrollRevealSection>

        <ScrollRevealSection className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {capabilityItems.slice(4).map((item, idx) => {
            const Icon = iconMap[idx + 4];
            return (
              <ScrollRevealItem key={item.id}>
                <article className="surface-card h-full p-5 shadow-[0_12px_30px_rgba(0,0,0,0.16)]">
                  <Icon className="h-5 w-5 text-[#1d1d1f]" />
                  <h4 className="mt-3 text-base font-semibold text-[#1d1d1f]">{item.title}</h4>
                  <p className="mt-1 text-sm text-[#6e6e73]">{item.description}</p>
                </article>
              </ScrollRevealItem>
            );
          })}
        </ScrollRevealSection>

        <ScrollRevealSection className="mt-6">
          <ScrollRevealItem>
            <div className="flex items-center justify-center">
              <div className="h-px w-16 bg-[#d2d2d7]" />
              <div className="mx-3 rounded-full border border-[#d2d2d7] bg-white px-3 py-1 text-xs font-medium text-[#6e6e73]">
                AI Oversight
              </div>
              <div className="h-px w-16 bg-[#d2d2d7]" />
            </div>
          </ScrollRevealItem>
        </ScrollRevealSection>

        <ScrollRevealSection className="mt-4">
          <ScrollRevealItem>
            <article className="surface-card border border-[#d2d2d7] bg-[#fafafa] p-6">
              <h4 className="text-lg font-semibold text-[#1d1d1f]">Execution Intelligence Layer</h4>
              <p className="mt-2 text-sm text-[#6e6e73]">
                Each capability runs under one coordinated intelligence layer that prioritizes phases, adapts scan behavior,
                validates execution signals, and helps keep operations stable while scans are running.
              </p>
              <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
                <div className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <p className="text-xs text-[#6e6e73]">Decisioning</p>
                  <p className="mt-1 text-sm font-medium text-[#1d1d1f]">Selects safest effective execution path per phase.</p>
                </div>
                <div className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <p className="text-xs text-[#6e6e73]">Adaptive control</p>
                  <p className="mt-1 text-sm font-medium text-[#1d1d1f]">Tunes runtime behavior based on live scan telemetry.</p>
                </div>
                <div className="rounded-xl border border-[#d2d2d7] bg-white p-3">
                  <p className="text-xs text-[#6e6e73]">Operational continuity</p>
                  <p className="mt-1 text-sm font-medium text-[#1d1d1f]">Supports pause/resume controls with continuous monitoring.</p>
                </div>
              </div>
            </article>
          </ScrollRevealItem>
        </ScrollRevealSection>
      </section>
    </main>
  );
}

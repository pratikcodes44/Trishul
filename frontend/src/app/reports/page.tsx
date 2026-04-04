'use client';

import { useEffect, useState } from 'react';
import { AppScaffold } from '@/components/layout/app-scaffold';
import { downloadReportMarkdown, getReport, getReportsAnalytics, getStats } from '@/lib/api-client';
import { isAuthenticated } from '@/lib/auth';
import type { ReportsResponse, StatsResponse } from '@/lib/api-contract';

export default function ReportsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [report, setReport] = useState<ReportsResponse | null>(null);
  const [scanId, setScanId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [analytics, setAnalytics] = useState<{ attacked_sites: number; completed_scans: number; findings_total: number; risk_index: number } | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) return;
    getStats().then(setStats).catch((err) => setError(err instanceof Error ? err.message : 'Failed to load stats'));
    getReportsAnalytics()
      .then((data) => setAnalytics(data.kpis))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load analytics'));
  }, []);

  async function fetchReport() {
    setError(null);
    setLoading(true);
    try {
      const data = await getReport(scanId, 'markdown');
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    const selectedScanId = report?.scan_id || scanId;
    if (!selectedScanId) return;
    setError(null);
    setDownloading(true);
    try {
      const { blob, filename } = await downloadReportMarkdown(selectedScanId);
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download markdown report');
    } finally {
      setDownloading(false);
    }
  }

  if (!isAuthenticated()) {
    return (
      <AppScaffold currentPage="reports" showSidebar>
        <main className="mx-auto max-w-4xl px-4 pb-10 pt-6 sm:px-6">
          <section className="surface-card p-6">
            <h2 className="text-lg font-semibold text-[#1d1d1f]">Reports & Analytics</h2>
            <p className="mt-2 text-sm text-[#6e6e73]">Please sign in first from /auth to view report data.</p>
          </section>
        </main>
      </AppScaffold>
    );
  }

  return (
    <AppScaffold currentPage="reports" showSidebar>
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-6 sm:px-6">
        <section className="surface-card p-5">
          <h2 className="text-lg font-semibold text-[#1d1d1f]">Reports & Analytics</h2>
          <p className="mt-1 text-sm text-[#6e6e73]">Live backend-connected reports and account statistics.</p>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
              <p className="text-xs text-[#6e6e73]">Total scans</p>
              <p className="text-xl font-semibold text-[#1d1d1f]">{stats?.stats.total_scans ?? '-'}</p>
            </div>
            <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
              <p className="text-xs text-[#6e6e73]">Vulnerabilities found</p>
              <p className="text-xl font-semibold text-[#1d1d1f]">{stats?.stats.vulnerabilities_found ?? '-'}</p>
            </div>
            <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
              <p className="text-xs text-[#6e6e73]">Critical alerts</p>
              <p className="text-xl font-semibold text-[#1d1d1f]">{stats?.stats.critical_alerts ?? '-'}</p>
            </div>
            <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
              <p className="text-xs text-[#6e6e73]">Attacked websites</p>
              <p className="text-xl font-semibold text-[#1d1d1f]">{analytics?.attacked_sites ?? '-'}</p>
            </div>
            <div className="rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-3">
              <p className="text-xs text-[#6e6e73]">Risk index</p>
              <p className="text-xl font-semibold text-[#1d1d1f]">{analytics?.risk_index ?? '-'}</p>
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <input
              className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
              placeholder="Enter scan id"
              value={scanId}
              onChange={(e) => setScanId(e.target.value)}
            />
            <button
              className="h-10 rounded-xl bg-[#1d1d1f] px-4 text-sm font-medium text-white disabled:opacity-60"
              onClick={fetchReport}
              disabled={!scanId || loading}
              type="button"
            >
              {loading ? 'Loading...' : 'Generate report'}
            </button>
          </div>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
          {report ? (
            <div className="mt-5 rounded-xl border border-[#d2d2d7] bg-[#fafafa] p-4">
              <p className="text-sm font-semibold text-[#1d1d1f]">Executive Summary</p>
              <p className="mt-2 text-sm text-[#6e6e73]">{report.executive_summary}</p>
              <p className="mt-2 text-xs text-[#6e6e73]">Generated at: {report.generated_at}</p>
              <button
                className="mt-3 h-9 rounded-xl bg-[#1d1d1f] px-3 text-sm font-medium text-white disabled:opacity-60"
                onClick={handleDownload}
                disabled={downloading}
                type="button"
              >
                {downloading ? 'Downloading...' : 'Download .md report'}
              </button>
            </div>
          ) : null}
        </section>
      </main>
    </AppScaffold>
  );
}

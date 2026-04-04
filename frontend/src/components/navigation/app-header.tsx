"use client";

import { useEffect, useMemo, useState } from "react";
import { Menu, Search } from "lucide-react";
import { AppPage } from "@/lib/types";
import { recentAttackedSites, searchAttackedSites } from "@/lib/api-client";
import { isAuthenticated } from "@/lib/auth";
import type { SearchSiteRecord } from "@/lib/api-contract";

interface AppHeaderProps {
  currentPage: AppPage;
  showBrand?: boolean;
  onOpenMobileNav?: () => void;
}

const pageTitles: Record<AppPage, string> = {
  landing: "Landing",
  operations: "Operations Dashboard",
  reports: "Reports & Analytics",
  auth: "Authentication",
};

export function AppHeader({
  currentPage,
  showBrand = true,
  onOpenMobileNav,
}: AppHeaderProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchSiteRecord[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const canSearch = useMemo(() => isAuthenticated(), []);

  useEffect(() => {
    if (!canSearch) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = query.trim()
          ? await searchAttackedSites(query.trim(), 8)
          : await recentAttackedSites(8);
        if (!cancelled) {
          setResults(res.results);
          setOpen(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, canSearch]);

  return (
    <header className="sticky top-0 z-40 border-b border-[#d2d2d7] bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <button
          onClick={onOpenMobileNav}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#d2d2d7] bg-white text-[#1d1d1f] md:hidden"
        >
          <Menu className="h-4 w-4" />
        </button>

        {showBrand ? (
          <div className="flex min-w-0 items-center gap-2">
            <span className="text-lg leading-none">🔱</span>
            <span className="truncate text-sm font-semibold tracking-[0.14em] text-[#1d1d1f]">TRISHUL</span>
          </div>
        ) : (
          <div className="w-1" />
        )}

        <div className="min-w-0 flex-1">
          <h1 className="truncate text-[15px] font-medium text-[#1d1d1f]">{pageTitles[currentPage]}</h1>
        </div>

        <label className="relative hidden w-[320px] items-center md:flex">
          <Search className="pointer-events-none absolute left-3 h-4 w-4 text-[#6e6e73]" />
          <input
            type="text"
            placeholder={canSearch ? "Search attacked websites" : "Sign in to search"}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 120)}
            disabled={!canSearch}
            className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-[#f5f5f7] pl-9 pr-3 text-sm text-[#1d1d1f] outline-none transition-colors focus:border-[#1d1d1f]"
          />
          {open && canSearch ? (
            <div className="absolute top-11 z-50 w-full rounded-xl border border-[#d2d2d7] bg-white p-2 shadow-sm">
              {loading ? (
                <p className="px-2 py-1 text-xs text-[#6e6e73]">Searching...</p>
              ) : results.length === 0 ? (
                <p className="px-2 py-1 text-xs text-[#6e6e73]">No attacked websites found.</p>
              ) : (
                <ul className="max-h-64 overflow-auto">
                  {results.map((item) => (
                    <li key={`${item.scan_id}-${item.target}`} className="rounded-lg px-2 py-2 hover:bg-[#f5f5f7]">
                      <p className="text-sm text-[#1d1d1f]">{item.target}</p>
                      <p className="text-[11px] text-[#6e6e73]">
                        {item.status} • {item.scan_type} • {item.scan_id.slice(0, 8)}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </label>

        <button className="ml-auto flex items-center gap-2 rounded-xl border border-[#d2d2d7] bg-white px-3 py-2 text-sm text-[#1d1d1f] transition-colors hover:bg-[#f5f5f7]">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#1d1d1f] text-xs font-medium text-white">
            M
          </span>
          <span className="hidden sm:inline">Manthan</span>
        </button>
      </div>
    </header>
  );
}

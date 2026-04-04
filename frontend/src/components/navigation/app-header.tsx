"use client";

import { Menu, Search } from "lucide-react";
import { AppPage } from "@/lib/types";

interface AppHeaderProps {
  currentPage: AppPage;
  showBrand?: boolean;
  onOpenMobileNav?: () => void;
}

const pageTitles: Record<AppPage, string> = {
  landing: "Landing",
  operations: "Operations Dashboard",
  reports: "Reports & Analytics",
};

export function AppHeader({
  currentPage,
  showBrand = true,
  onOpenMobileNav,
}: AppHeaderProps) {
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

        <label className="relative hidden w-[280px] items-center md:flex">
          <Search className="pointer-events-none absolute left-3 h-4 w-4 text-[#6e6e73]" />
          <input
            type="text"
            placeholder="Search"
            className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-[#f5f5f7] pl-9 pr-3 text-sm text-[#1d1d1f] outline-none transition-colors focus:border-[#1d1d1f]"
          />
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

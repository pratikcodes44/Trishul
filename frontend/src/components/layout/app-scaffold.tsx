"use client";

import { ReactNode, useState } from "react";
import { AppHeader } from "@/components/navigation/app-header";
import { MobileNavPanel } from "@/components/navigation/mobile-nav-panel";
import { SideNav } from "@/components/navigation/side-nav";
import { AppPage } from "@/lib/types";

interface AppScaffoldProps {
  currentPage: AppPage;
  showSidebar: boolean;
  children: ReactNode;
}

export function AppScaffold({ currentPage, showSidebar, children }: AppScaffoldProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">
      <AppHeader currentPage={currentPage} showBrand onOpenMobileNav={() => setMobileNavOpen(true)} />
      <MobileNavPanel open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      {showSidebar ? (
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-7xl">
          <SideNav collapsed={collapsed} onToggle={() => setCollapsed((prev) => !prev)} />
          <div className="min-w-0 flex-1">{children}</div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}

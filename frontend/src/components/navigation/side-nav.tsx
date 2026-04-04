"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { navItems } from "@/components/navigation/nav-config";

interface SideNavProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function SideNav({ collapsed, onToggle }: SideNavProps) {
  const pathname = usePathname();
  return (
    <aside
      className={`hidden border-r border-[#d2d2d7] bg-white p-3 md:block ${
        collapsed ? "w-[84px]" : "w-[240px]"
      }`}
    >
      <button
        onClick={onToggle}
        className="mb-3 flex h-10 w-full items-center justify-center rounded-xl border border-[#d2d2d7] bg-[#f5f5f7] text-[#1d1d1f] transition-colors hover:bg-[#ebebee]"
      >
        {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
      </button>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.id}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={`group flex h-11 w-full items-center rounded-xl px-3 text-sm transition-colors ${
                  active ? "bg-[#1d1d1f] text-white" : "text-[#1d1d1f] hover:bg-[#f5f5f7]"
                }`}
            >
                <Icon className={`h-4 w-4 ${collapsed ? "mx-auto" : ""}`} />
                {!collapsed && <span className="ml-3">{item.label}</span>}
              </Link>
            );
          })}
        </nav>
    </aside>
  );
}

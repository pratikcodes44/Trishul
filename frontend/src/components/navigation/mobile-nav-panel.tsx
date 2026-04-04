"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { navItems } from "@/components/navigation/nav-config";

interface MobileNavPanelProps {
  open: boolean;
  onClose: () => void;
}

export function MobileNavPanel({
  open,
  onClose,
}: MobileNavPanelProps) {
  const pathname = usePathname();
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 md:hidden">
      <div className="h-full w-[270px] border-r border-[#d2d2d7] bg-white p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>🔱</span>
            <span className="text-sm font-semibold tracking-[0.14em] text-[#1d1d1f]">TRISHUL</span>
          </div>
          <button
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#d2d2d7] text-[#1d1d1f]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.id}
                href={item.href}
                onClick={onClose}
                className={`flex h-11 w-full items-center rounded-xl px-3 text-sm ${
                  active ? "bg-[#1d1d1f] text-white" : "text-[#1d1d1f] hover:bg-[#f5f5f7]"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="ml-3">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <button aria-label="close overlay" onClick={onClose} className="absolute inset-0 -z-10 h-full w-full" />
    </div>
  );
}

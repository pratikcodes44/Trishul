import { House, Radar, FileBarChart2 } from "lucide-react";
import type { AppPage } from "@/lib/types";

export const navItems: Array<{
  id: AppPage;
  label: string;
  href: `/${string}` | "/";
  icon: typeof House;
}> = [
  { id: "landing", label: "Landing", href: "/", icon: House },
  { id: "operations", label: "Operations", href: "/operations", icon: Radar },
  { id: "reports", label: "Reports", href: "/reports", icon: FileBarChart2 },
];

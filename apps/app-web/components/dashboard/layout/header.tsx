"use client";

import * as React from "react";
import Link from "next/link";
import { KeyRound, Settings } from "lucide-react";
import { useDashboard } from "../context/dashboard-context";
import { ThemeToggle } from "@/components/theme-toggle";

interface DashboardHeaderProps {
  activeTab?: "Monitoring" | "Dashboards" | "Alerts";
  onTabChange?: (tab: "Monitoring" | "Dashboards" | "Alerts") => void;
  onOpenAlertModal?: () => void;
  onOpenDashboardModal?: () => void;
}

export function DashboardHeader({
  activeTab,
  onTabChange,
  onOpenAlertModal,
  onOpenDashboardModal,
}: DashboardHeaderProps) {
  const { isLive, setIsLive, lastUpdated } = useDashboard();

  return (
    <header className="border-b border-border bg-background/95 backdrop-blur-md px-6 py-2.5 flex items-center justify-between transition-colors">
      {/* Platform Title & Subtitle */}
      <div className="flex items-center gap-2.5">
        <h1 className="font-semibold text-sm text-foreground tracking-tight">ASI:Telemetry</h1>
        <span className="text-border hidden sm:inline">|</span>
        <span className="text-xs text-muted-foreground hidden sm:inline">
          Observability &amp; Monitoring Platform
        </span>
      </div>

      {/* Global Controls: Last updated, Live stream toggle, and Theme Switcher */}
      <div className="flex items-center gap-2">

        {/* API Keys Shortcut */}
        <Link
          href="/api-keys"
          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-2.5 text-xs font-medium shadow-xs hover:bg-muted hover:text-foreground"
          title="Manage API Keys"
        >
          <KeyRound className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">API Keys</span>
        </Link>

        {/* Profile & Settings Shortcut */}
        <Link
          href="/settings"
          className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-2.5 text-xs font-medium shadow-xs hover:bg-muted hover:text-foreground"
          title="Profile & Settings"
        >
          <Settings className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Settings</span>
        </Link>

        {/* Light & Dark Mode Switch */}
        <ThemeToggle />
      </div>
    </header>
  );
}

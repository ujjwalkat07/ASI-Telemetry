"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  Boxes,
  ChevronDown,
  Gauge,
  Home,
  KeyRound,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getStoredUser, clearStoredUser } from "@/lib/auth";

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  badge?: string;
  isPlus?: boolean;
  hasSub?: boolean;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

interface DashboardSidebarProps {
  activeNav?: string;
  onNavChange?: (nav: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function DashboardSidebar({
  activeNav,
  onNavChange,
  collapsed = false,
  onToggleCollapse,
}: DashboardSidebarProps) {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = React.useState("");

  const [currentUser, setCurrentUser] = React.useState<ReturnType<typeof getStoredUser>>(null);

  React.useEffect(() => {
    setCurrentUser(getStoredUser());
    const handleUserUpdate = (e: any) => {
      if (e.detail) {
        setCurrentUser(e.detail);
      } else {
        setCurrentUser(getStoredUser());
      }
    };
    window.addEventListener("asi-user-updated", handleUserUpdate);
    return () => window.removeEventListener("asi-user-updated", handleUserUpdate);
  }, []);

  const navigationGroups: NavGroup[] = [
    {
      group: "Application",
      items: [
        { label: "Agents", href: "/all-applications", icon: Boxes },
        { label: "Dashboard", href: "/dashboard", icon: Home },
      ],
    },
    {
      group: "Observability",
      items: [
        { label: "Tool Monitoring", href: "/tool-monitoring", icon: Gauge },
        { label: "Tool Tracing", href: "/tracing", icon: Activity, badge: "1" },
        { label: "LLM Tracing", href: "/llm-traces", icon: Bot, badge: "New" },
        { label: "LLM Monitoring", href: "/llm-monitoring", icon: Bot },
      ],
    },
    {
      group: "Access & Security",
      items: [
        { label: "API Keys", href: "/api-keys", icon: KeyRound, badge: "Active" },
        { label: "Profile & Settings", href: "/settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-border bg-sidebar text-sidebar-foreground transition-all duration-300 ease-in-out shrink-0 select-none",
        collapsed ? "w-16" : "w-64 min-w-[16rem]"
      )}
    >
      {/* Brand & Workspace Switcher Header */}
      <div className="flex h-14 items-center justify-between border-b border-border px-3.5">
        {collapsed ? (
          <div className="flex w-full items-center justify-center">
            <button
              onClick={onToggleCollapse}
              className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Expand sidebar"
            >
              <PanelLeftOpen className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs shrink-0">
                <Activity className="h-4 w-4" />
              </div>
              <Link href="/">
                <div className="flex flex-col truncate">
                  <div className="flex items-center gap-1.5 font-bold text-sm tracking-tight text-foreground">
                    <span className="font-semibold text-sm">ASI:Telemetry</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground -mt-0.5">
                    Observability Platform
                  </span>
                </div>
              </Link>
            </div>

            <button
              onClick={onToggleCollapse}
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Collapse sidebar"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </>
        )}
      </div>

      {/* Quick Search */}
      {!collapsed ? (
        <div className="px-3 pt-3 pb-1">
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-full rounded-md border border-input bg-background pl-8 pr-12 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-colors"
            />
            <div className="absolute right-2 flex items-center gap-0.5 rounded border border-border bg-muted px-1 py-0.5 text-[9px] text-muted-foreground font-mono">
              <span>Ctrl</span>
              <span>K</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex justify-center pt-3 pb-1">
          <button
            onClick={onToggleCollapse}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-input bg-background text-muted-foreground hover:text-foreground hover:border-border transition-colors"
            title="Search (Ctrl+K)"
          >
            <Search className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Navigation Menu List */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4">
        {navigationGroups.map((group, idx) => (
          <div key={idx} className="space-y-0.5">
            {!collapsed && (
              <div className="px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {group.group}
              </div>
            )}
            {group.items.map((item, itemIdx) => {
              const Icon = item.icon;
              const isActive =
                activeNav === item.label ||
                (item.href === "/" && pathname === "/") ||
                (item.href !== "/" && (pathname === item.href || pathname?.startsWith(item.href + "/")));

              return (
                <Link
                  key={itemIdx}
                  href={item.href}
                  onClick={() => onNavChange?.(item.label)}
                  title={collapsed ? item.label : undefined}
                  className={cn(
                    "group relative flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    collapsed && "justify-center px-0 h-9 w-full"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      isActive
                        ? "text-primary-foreground"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />

                  {!collapsed && (
                    <>
                      <span className="truncate flex-1 text-left">{item.label}</span>

                      {item.badge && (
                        <span className={cn(
                          "flex h-4 min-w-4 items-center justify-center rounded-full px-1.5 text-[10px] font-mono",
                          isActive ? "bg-primary-foreground/20 text-primary-foreground" : "border border-border/80 bg-muted text-muted-foreground"
                        )}>
                          {item.badge}
                        </span>
                      )}

                      {item.isPlus && (
                        <span className="rounded bg-muted px-1.5 py-0.5 text-[9px] font-semibold text-foreground border border-border">
                          Plus
                        </span>
                      )}

                      {item.hasSub && (
                        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                    </>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer / System Status & Settings */}
      <div className="border-border p-2 space-y-1 bg-sidebar">


        {!collapsed && (
          <div className="flex items-center justify-between gap-2 px-2 py-1.5 border-t border-border pt-2">
            <Link
              href="/settings"
              className="flex items-center gap-2.5 overflow-hidden flex-1 group hover:opacity-80 transition-opacity"
              title="Account Profile & Settings"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold text-xs shrink-0 shadow-xs">
                {currentUser?.name
                  ? currentUser.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()
                  : "U"}
              </div>
              <div className="flex flex-col truncate">
                <span className="text-xs font-medium text-foreground truncate group-hover:underline">
                  {currentUser?.name || "My Account"}
                </span>
                {currentUser?.email && (
                  <span className="text-[10px] text-muted-foreground truncate">
                    {currentUser.email}
                  </span>
                )}
              </div>
            </Link>

            <Link
              href="/login"
              onClick={() => clearStoredUser()}
              className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-destructive hover:bg-muted transition-colors shrink-0"
              title="Sign Out / Switch Account"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}

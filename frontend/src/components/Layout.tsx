"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";

type LayoutProps = {
  title: string;
  children: ReactNode;
};

const STORAGE_KEY = "focus.sidebarCollapsed";

export default function Layout({ title, children }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "1") {
        setCollapsed(true);
      }
    } catch {
      // Ignore storage failures (private mode, blocked storage, etc.)
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch {
      // Ignore storage failures (private mode, blocked storage, etc.)
    }
  }, [collapsed]);

  const toggleCollapsed = () => setCollapsed((previous) => !previous);

  return (
    <div className="min-h-screen bg-slate-50">
      <aside
        className={[
          "fixed inset-y-0 left-0 z-40 hidden border-r border-slate-200 bg-white md:flex",
          "transition-[width] duration-200 ease-out",
          collapsed ? "w-20" : "w-72"
        ].join(" ")}
      >
        <Sidebar
          variant="desktop"
          collapsed={collapsed}
          onToggleCollapsed={toggleCollapsed}
        />
      </aside>

      <div
        className={[
          "min-h-screen transition-[padding] duration-200 ease-out",
          collapsed ? "md:pl-20" : "md:pl-72"
        ].join(" ")}
      >
        <Topbar title={title} collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}

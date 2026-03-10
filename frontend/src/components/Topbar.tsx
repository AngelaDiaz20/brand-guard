"use client";

import { useState } from "react";

import Sidebar from "@/components/Sidebar";

type TopbarProps = {
  title: string;
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

export default function Topbar({ title, collapsed, onToggleCollapsed }: TopbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 md:hidden"
            aria-label="Abrir menu"
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>

          <button
            type="button"
            onClick={onToggleCollapsed}
            className="hidden rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 md:inline-flex"
            aria-label={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
            title={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className={collapsed ? "h-5 w-5 rotate-180" : "h-5 w-5"}
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14.25 4.5 6.75 12l7.5 7.5"
              />
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 4.5v15" />
            </svg>
          </button>

          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.28em] text-slate-500">
              SODIMAC
            </p>
            <h1 className="mt-0.5 text-lg font-semibold text-slate-900">{title}</h1>
          </div>
        </div>

        <div className="hidden items-center gap-2 sm:flex">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            UI Placeholder
          </span>
        </div>
      </div>

      {mobileOpen && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-50 cursor-default bg-slate-900/40 backdrop-blur-sm"
            aria-label="Cerrar menu"
            onClick={() => setMobileOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl">
            <Sidebar variant="mobile" onNavigate={() => setMobileOpen(false)} />
          </div>
        </>
      )}
    </header>
  );
}

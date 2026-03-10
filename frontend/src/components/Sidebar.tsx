"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = {
  href: string;
  label: string;
  icon: ReactNode;
};

type SidebarVariant = "desktop" | "mobile";

type SidebarProps = {
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  onNavigate?: () => void;
  variant?: SidebarVariant;
};

const navItems: NavItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    // Heroicons-inspired: squares-2x2
    icon: (
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M4 4.75A.75.75 0 0 1 4.75 4h4.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 4 9.25v-4.5ZM14 4.75a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 14 9.25v-4.5ZM4 14.75a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 4 19.25v-4.5ZM14 14.75a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-4.5a.75.75 0 0 1-.75-.75v-4.5Z"
        />
      </svg>
    )
  },
  {
    href: "/analizar",
    label: "Analizar Activo",
    // Heroicons-inspired: magnifying-glass
    icon: (
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M10.5 18a7.5 7.5 0 1 0 0-15 7.5 7.5 0 0 0 0 15Z"
        />
        <path strokeLinecap="round" strokeLinejoin="round" d="M16 16l5 5" />
      </svg>
    )
  },
  {
    href: "/lineamientos",
    label: "Lineamientos",
    // Heroicons-inspired: document-text
    icon: (
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 7.5v11.25A2.25 2.25 0 0 1 17.25 21H6.75A2.25 2.25 0 0 1 4.5 18.75V5.25A2.25 2.25 0 0 1 6.75 3h7.5L19.5 7.5Z"
        />
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 13.5h6M9 16.5h6M9 10.5h3" />
      </svg>
    )
  }
];

function isRouteActive(pathname: string, href: string) {
  if (pathname === href) {
    return true;
  }
  return pathname.startsWith(`${href}/`);
}

export default function Sidebar({
  collapsed = false,
  onToggleCollapsed,
  onNavigate,
  variant = "desktop"
}: SidebarProps) {
  const pathname = usePathname() ?? "";
  const effectiveCollapsed = variant === "desktop" ? collapsed : false;

  return (
    <div className="flex h-full flex-col">
      <div className={effectiveCollapsed ? "px-3 py-5" : "px-6 py-5"}>
        <div className="flex items-center justify-between gap-2">
          {effectiveCollapsed ? (
            <div className="mx-auto grid h-10 w-10 place-items-center rounded-xl bg-slate-900 text-sm font-semibold text-white">
              F
            </div>
          ) : (
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.28em] text-slate-500">
                SODIMAC
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-900">Focus</p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 px-3 pb-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const active = isRouteActive(pathname, item.href);
            const base =
              "group relative flex items-center rounded-xl px-3 py-2.5 text-sm font-medium transition";
            const layout = effectiveCollapsed ? "justify-center gap-0" : "gap-3";
            const colors = active
              ? "bg-slate-900 text-white shadow-sm"
              : "text-slate-700 hover:bg-slate-100 hover:text-slate-900";

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  title={item.label}
                  onClick={onNavigate ? () => onNavigate() : undefined}
                  className={`${base} ${layout} ${colors}`}
                >
                  <span
                    className={
                      active
                        ? "grid h-9 w-9 place-items-center rounded-lg bg-white/10 text-white"
                        : "grid h-9 w-9 place-items-center rounded-lg bg-slate-50 text-slate-600 transition group-hover:bg-white group-hover:text-slate-800"
                    }
                  >
                    {item.icon}
                  </span>
                  <span className={effectiveCollapsed ? "sr-only" : "truncate"}>
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {variant === "desktop" && onToggleCollapsed && (
        <div className={effectiveCollapsed ? "px-3 py-4" : "px-4 py-4"}>
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            title={effectiveCollapsed ? "Expandir sidebar" : "Colapsar sidebar"}
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className={effectiveCollapsed ? "h-5 w-5 rotate-180" : "h-5 w-5"}
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
            <span className={effectiveCollapsed ? "sr-only" : ""}>
              {effectiveCollapsed ? "Expandir" : "Colapsar"}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

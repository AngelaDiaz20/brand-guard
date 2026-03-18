"use client";

import type { PropsWithChildren, ReactNode } from "react";
import { useId, useState } from "react";

interface DisclosureSectionProps extends PropsWithChildren {
  title: string;
  defaultOpen?: boolean;
  badge?: ReactNode;
}

export function DisclosureSection({ title, defaultOpen = false, badge, children }: DisclosureSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const contentId = useId();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 rounded-2xl px-5 py-4 text-left"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setOpen((previous) => !previous)}
      >
        <div className="flex min-w-0 items-center gap-3">
          <h3 className="truncate text-base font-semibold text-slate-900">{title}</h3>
          {badge}
        </div>

        <span className="shrink-0 text-slate-500" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div id={contentId} className="border-t border-slate-200 px-5 py-5">
          {children}
        </div>
      )}
    </section>
  );
}


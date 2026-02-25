import type { PropsWithChildren } from "react";

interface SectionCardProps extends PropsWithChildren {
  className?: string;
}

export function SectionCard({ children, className = "" }: SectionCardProps) {
  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ${className}`.trim()}
    >
      {children}
    </section>
  );
}

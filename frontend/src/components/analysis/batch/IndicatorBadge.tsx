import type { IndicatorState } from "@/types/analysisBatch";

const STATE_STYLES: Record<IndicatorState, { dot: string; className: string; label: string }> = {
  ok: { dot: "bg-emerald-500", className: "border-emerald-200 bg-emerald-50 text-emerald-800", label: "OK" },
  alerta: { dot: "bg-amber-500", className: "border-amber-200 bg-amber-50 text-amber-900", label: "Alerta" },
  error: { dot: "bg-red-500", className: "border-red-200 bg-red-50 text-red-800", label: "Error" },
  no_aplica: { dot: "bg-slate-300", className: "border-slate-200 bg-slate-50 text-slate-600", label: "No aplica" }
};

export function IndicatorBadge({ label, state }: { label: string; state: IndicatorState }) {
  const style = STATE_STYLES[state];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium ${style.className}`}
      title={`${label}: ${style.label}`}
    >
      <span className={`h-2 w-2 rounded-full ${style.dot}`} aria-hidden="true" />
      <span className="truncate">{label}</span>
    </span>
  );
}

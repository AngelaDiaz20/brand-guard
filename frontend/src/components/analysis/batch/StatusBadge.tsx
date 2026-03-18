import type { AnalysisStatus } from "@/types/analysisBatch";

const STATUS_STYLES: Record<AnalysisStatus, { label: string; className: string }> = {
  ok: { label: "OK", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  alerta: { label: "Alerta", className: "border-amber-200 bg-amber-50 text-amber-800" },
  error: { label: "Error", className: "border-red-200 bg-red-50 text-red-700" }
};

export function StatusBadge({ status }: { status: AnalysisStatus }) {
  const style = STATUS_STYLES[status];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${style.className}`}
    >
      {style.label}
    </span>
  );
}


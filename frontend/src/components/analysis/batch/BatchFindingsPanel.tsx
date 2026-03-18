import type { BatchFinding } from "@/utils/analysisBatch";

const SEVERITY_STYLES: Record<BatchFinding["severity"], { className: string; label: string }> = {
  ok: { className: "border-emerald-200 bg-emerald-50 text-emerald-800", label: "OK" },
  alerta: { className: "border-amber-200 bg-amber-50 text-amber-900", label: "Alerta" },
  error: { className: "border-red-200 bg-red-50 text-red-800", label: "Error" }
};

export function BatchFindingsPanel({ findings }: { findings: BatchFinding[] }) {
  if (findings.length === 0) {
    return null;
  }

  const top = findings.slice(0, 6);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Hallazgos principales del lote</h3>
      <p className="mt-1 text-xs text-slate-600">
        Resumen por frecuencia a partir de las validaciones y el OCR de cada pieza.
      </p>

      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {top.map((finding) => {
          const style = SEVERITY_STYLES[finding.severity];
          return (
            <li
              key={finding.key}
              className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-800">{finding.label}</p>
                <p className="text-xs text-slate-600">
                  {finding.count} pieza{finding.count === 1 ? "" : "s"}
                </p>
              </div>
              <span className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold ${style.className}`}>
                {style.label}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}


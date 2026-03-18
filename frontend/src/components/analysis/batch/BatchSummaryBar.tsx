import type { BatchSummary } from "@/types/analysisBatch";

function interpretScore(score: number): string {
  if (score >= 90) return "Excelente consistencia general";
  if (score >= 75) return "Buen cumplimiento general";
  if (score >= 60) return "Cumplimiento medio, conviene revisar";
  return "Lote con varias observaciones";
}

export function BatchSummaryBar({ summary }: { summary: BatchSummary }) {
  const scoreText =
    summary.completadas > 0 ? `${summary.scorePromedio}/100` : "No disponible";

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Puntaje general del lote</p>
        <div className="mt-2 flex items-end justify-between gap-4">
          <p className="text-3xl font-bold text-slate-900">{scoreText}</p>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
            {summary.analizadas}/{summary.total} analizadas
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-600">
          {summary.completadas > 0 ? interpretScore(summary.scorePromedio) : "Calculado al finalizar piezas."}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 lg:col-span-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Resumen del lote</h2>
            <p className="text-xs text-slate-600">
              {summary.total} seleccionada{summary.total === 1 ? "" : "s"} · {summary.pendientes} pendiente
              {summary.pendientes === 1 ? "" : "s"} · {summary.enProceso} en proceso · {summary.conError} con error
            </p>
          </div>

          <div className="text-right">
            <p className="text-sm font-semibold text-slate-900">{summary.progresoPercent}%</p>
            <p className="text-xs text-slate-600">
              {summary.analizadas} de {summary.total} piezas analizadas
            </p>
          </div>
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-300"
            style={{ width: `${summary.progresoPercent}%` }}
          />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
            Pendientes: {summary.pendientes}
          </span>
          <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            En proceso: {summary.enProceso}
          </span>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            Completadas: {summary.completadas}
          </span>
          <span className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
            Con error: {summary.conError}
          </span>

          {summary.completadas > 0 && (
            <>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Correctas: {summary.ok}
              </span>
              <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                Con alertas: {summary.alerta}
              </span>
              <span className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                Errores críticos: {summary.error}
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                Alertas relevantes: {summary.conAlertas}
              </span>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

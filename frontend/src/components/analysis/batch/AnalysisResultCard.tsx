"use client";

import type { PropsWithChildren } from "react";

import type { AnalysisCardData, AnalysisItemState } from "@/types/analysisBatch";
import { IndicatorBadge } from "@/components/analysis/batch/IndicatorBadge";
import { StatusBadge } from "@/components/analysis/batch/StatusBadge";

interface AnalysisResultCardProps extends PropsWithChildren {
  card: AnalysisCardData;
  itemState: AnalysisItemState;
  progressPercent?: number;
  expanded: boolean;
  onToggle: () => void;
}

const STATE_STYLES: Record<
  AnalysisItemState,
  { label: string; className: string; text: (progressPercent?: number) => string }
> = {
  pendiente: {
    label: "Pendiente",
    className: "border-slate-200 bg-slate-50 text-slate-700",
    text: () => "Pendiente"
  },
  subiendo: {
    label: "Subiendo",
    className: "border-blue-200 bg-blue-50 text-blue-700",
    text: (progressPercent) =>
      typeof progressPercent === "number" ? `Subiendo ${progressPercent}%` : "Subiendo"
  },
  analizando: {
    label: "Analizando",
    className: "border-blue-200 bg-blue-50 text-blue-700",
    text: (progressPercent) =>
      typeof progressPercent === "number" ? `Analizando ${progressPercent}%` : "Analizando"
  },
  listo: {
    label: "Completado",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    text: () => "Completado"
  },
  error: {
    label: "Error",
    className: "border-red-200 bg-red-50 text-red-700",
    text: () => "Error"
  }
};

export function AnalysisResultCard({
  card,
  itemState,
  progressPercent,
  expanded,
  onToggle,
  children
}: AnalysisResultCardProps) {
  const stateStyle = STATE_STYLES[itemState];
  const hasResult = itemState === "listo";

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-4">
          <div className="h-16 w-16 shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
            {card.fileType === "image" ? (
              <img
                src={card.previewUrl}
                alt={`Miniatura de ${card.fileName}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="grid h-full w-full place-items-center text-xs font-semibold text-slate-500">
                PDF
              </div>
            )}
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="truncate text-sm font-semibold text-slate-900">{card.fileName}</p>
              <span
                className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${stateStyle.className}`}
                title={stateStyle.label}
              >
                {stateStyle.text(progressPercent)}
              </span>
              {hasResult && <StatusBadge status={card.statusGeneral} />}
              {hasResult && (
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700">
                  Puntaje: {card.scoreGeneral}/100
                </span>
              )}
            </div>

            <p className="mt-1 text-xs text-slate-600">
              Formato: {hasResult ? card.format : "—"}
              {hasResult && card.pieceType ? ` · Pieza: ${card.pieceType}` : ""}
            </p>

            {hasResult && (
              <div className="mt-3 flex flex-wrap gap-2">
                {card.indicators.map((indicator) => (
                  <IndicatorBadge key={indicator.key} label={indicator.label} state={indicator.state} />
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="shrink-0">
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={expanded}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {expanded ? "Ocultar detalle" : "Ver detalle"}
          </button>
        </div>
      </div>

      {expanded && <div className="border-t border-slate-200 bg-slate-50 px-5 py-5">{children}</div>}
    </article>
  );
}

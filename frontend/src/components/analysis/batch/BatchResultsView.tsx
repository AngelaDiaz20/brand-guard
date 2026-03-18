"use client";

import { useEffect, useMemo, useState } from "react";

import type { AnalysisItem } from "@/types/analysisBatch";
import { buildBatchFindings, buildBatchSummary, buildCardDataFromItem } from "@/utils/analysisBatch";

import { AnalysisDetailPanel } from "@/components/analysis/batch/AnalysisDetailPanel";
import { BatchFindingsPanel } from "@/components/analysis/batch/BatchFindingsPanel";
import { AnalysisResultCard } from "@/components/analysis/batch/AnalysisResultCard";
import { BatchSummaryBar } from "@/components/analysis/batch/BatchSummaryBar";
import { ImagePreview } from "@/components/preview/ImagePreview";

interface BatchResultsViewProps {
  items: AnalysisItem[];
  onRetryItem?: (id: string) => void;
  isBusy?: boolean;
}

export function BatchResultsView({
  items,
  onRetryItem,
  isBusy = false
}: BatchResultsViewProps) {
  const [filter, setFilter] = useState<"todas" | "correctas" | "alertas" | "error">("todas");
  const [order, setOrder] = useState<"nombre" | "estado" | "score_alto" | "score_bajo">("estado");
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  const cardById = useMemo(() => {
    const map = new Map<string, ReturnType<typeof buildCardDataFromItem>>();
    items.forEach((item) => map.set(item.id, buildCardDataFromItem(item)));
    return map;
  }, [items]);

  const summary = useMemo(() => buildBatchSummary(items, items.map((item) => cardById.get(item.id)!)), [items, cardById]);
  const findings = useMemo(() => buildBatchFindings(items), [items]);

  const visibleItems = useMemo(() => {
    const filtered = items.filter((item) => {
      const card = cardById.get(item.id);
      if (!card) return true;

      if (filter === "todas") return true;
      if (filter === "correctas") return item.state === "listo" && card.statusGeneral === "ok";
      if (filter === "alertas") return item.state === "listo" && card.statusGeneral === "alerta";
      return item.state === "error" || (item.state === "listo" && card.statusGeneral === "error");
    });

    const stateRank: Record<AnalysisItem["state"], number> = {
      subiendo: 0,
      analizando: 1,
      pendiente: 2,
      error: 3,
      listo: 4
    };

    const getScore = (item: AnalysisItem) => {
      const card = cardById.get(item.id);
      if (!card || item.state !== "listo") return null;
      return card.scoreGeneral;
    };

    const sorted = [...filtered].sort((a, b) => {
      if (order === "estado") {
        return stateRank[a.state] - stateRank[b.state] || a.input.fileName.localeCompare(b.input.fileName);
      }
      if (order === "nombre") {
        return a.input.fileName.localeCompare(b.input.fileName);
      }
      if (order === "score_alto") {
        const sa = getScore(a);
        const sb = getScore(b);
        if (sa === null && sb === null) return a.input.fileName.localeCompare(b.input.fileName);
        if (sa === null) return 1;
        if (sb === null) return -1;
        return sb - sa || a.input.fileName.localeCompare(b.input.fileName);
      }
      const sa = getScore(a);
      const sb = getScore(b);
      if (sa === null && sb === null) return a.input.fileName.localeCompare(b.input.fileName);
      if (sa === null) return 1;
      if (sb === null) return -1;
      return sa - sb || a.input.fileName.localeCompare(b.input.fileName);
    });

    return sorted;
  }, [items, cardById, filter, order]);

  useEffect(() => {
    setExpandedIds((previous) => previous.filter((id) => items.some((item) => item.id === id)));
  }, [items]);

  useEffect(() => {
    if (expandedIds.length > 0) {
      return;
    }
    const focus = visibleItems.find((item) => item.state === "subiendo" || item.state === "analizando");
    if (focus) {
      setExpandedIds([focus.id]);
    }
  }, [visibleItems, expandedIds.length]);

  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
        Aún no hay análisis. Sube una o más imágenes y haz clic en Analizar.
      </div>
    );
  }

  const visibleIds = visibleItems.map((item) => item.id);
  const allExpanded = visibleIds.length > 0 && visibleIds.every((id) => expandedIds.includes(id));

  return (
    <div className="space-y-4">
      <BatchSummaryBar summary={summary} />
      <BatchFindingsPanel findings={findings} />

      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Filtros</span>
          <button
            type="button"
            onClick={() => setFilter("todas")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              filter === "todas" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-700"
            }`}
          >
            Todas
          </button>
          <button
            type="button"
            onClick={() => setFilter("correctas")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              filter === "correctas" ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-200 bg-white text-slate-700"
            }`}
          >
            Correctas
          </button>
          <button
            type="button"
            onClick={() => setFilter("alertas")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              filter === "alertas" ? "border-amber-600 bg-amber-600 text-white" : "border-slate-200 bg-white text-slate-700"
            }`}
          >
            Con alertas
          </button>
          <button
            type="button"
            onClick={() => setFilter("error")}
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              filter === "error" ? "border-red-600 bg-red-600 text-white" : "border-slate-200 bg-white text-slate-700"
            }`}
          >
            Con error
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500" htmlFor="batch-order">
            Orden
          </label>
          <select
            id="batch-order"
            value={order}
            onChange={(event) => setOrder(event.target.value as typeof order)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
          >
            <option value="estado">Estado</option>
            <option value="nombre">Nombre</option>
            <option value="score_alto">Puntaje más alto</option>
            <option value="score_bajo">Puntaje más bajo</option>
          </select>

          <button
            type="button"
            onClick={() => setExpandedIds(allExpanded ? [] : visibleIds)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            {allExpanded ? "Contraer todas" : "Expandir todas"}
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {visibleItems.map((item) => {
          const card = cardById.get(item.id)!;
          const expanded = expandedIds.includes(item.id);

          return (
            <AnalysisResultCard
              key={item.id}
              card={card}
              itemState={item.state}
              progressPercent={item.state === "subiendo" ? item.progressPercent : undefined}
              expanded={expanded}
              onToggle={() =>
                setExpandedIds((previous) =>
                  previous.includes(item.id) ? previous.filter((id) => id !== item.id) : [...previous, item.id]
                )
              }
            >
              {item.state === "listo" ? (
                <AnalysisDetailPanel
                  result={item.output}
                  preview={{ fileUrl: item.input.previewUrl, fileType: item.input.fileType }}
                />
              ) : item.state === "subiendo" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-medium text-blue-700">
                    Subiendo esta imagen
                    {typeof item.progressPercent === "number" ? ` · ${item.progressPercent}%` : "..."}
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${Math.max(0, Math.min(100, item.progressPercent ?? 0))}%` }}
                    />
                  </div>
                  <ImagePreview fileUrl={item.input.previewUrl} fileType={item.input.fileType} result={null} />
                </div>
              ) : item.state === "analizando" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-medium text-blue-700">
                    Analizando esta imagen...
                  </div>
                  <ImagePreview fileUrl={item.input.previewUrl} fileType={item.input.fileType} result={null} />
                </div>
              ) : item.state === "error" ? (
                <div className="space-y-3">
                  <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {item.error}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {onRetryItem && (
                      <button
                        type="button"
                        disabled={isBusy}
                        onClick={() => onRetryItem(item.id)}
                        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Reintentar
                      </button>
                    )}
                    <span className="text-xs text-slate-500">
                      Puedes reintentar sin afectar las demás imágenes.
                    </span>
                  </div>
                  <ImagePreview fileUrl={item.input.previewUrl} fileType={item.input.fileType} result={null} />
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                    Pendiente de análisis.
                  </div>
                  <ImagePreview fileUrl={item.input.previewUrl} fileType={item.input.fileType} result={null} />
                </div>
              )}
            </AnalysisResultCard>
          );
        })}
      </div>
    </div>
  );
}

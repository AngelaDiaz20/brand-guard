"use client";

import type { PriceBlockAnalysis, StructuredFields } from "@/types/analysis";

type PillVariant = "ok" | "error" | "warning" | "na";

function StatusPill({ variant, label }: { variant: PillVariant; label: string }) {
  const styles =
    variant === "ok"
      ? "bg-emerald-200 text-emerald-800"
      : variant === "warning"
        ? "bg-amber-200 text-amber-900"
        : variant === "na"
          ? "bg-slate-200 text-slate-800"
          : "bg-red-200 text-red-800";

  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${styles}`}>{label}</span>;
}

function fieldStatusToPill(status: string): { variant: PillVariant; label: string } {
  if (status === "detected") return { variant: "ok", label: "Detectado" };
  if (status === "ambiguous") return { variant: "warning", label: "Ambiguo" };
  if (status === "not_applicable") return { variant: "na", label: "No aplica" };
  if (status === "not_detected") return { variant: "na", label: "No detectado" };
  return { variant: "na", label: status || "—" };
}

function colorLabel(color: string) {
  if (color === "red") return "Rojo";
  if (color === "black") return "Negro";
  if (color === "indeterminate") return "Indeterminado";
  return color || "Indeterminado";
}

export function StructuredFieldsPanel({
  fields,
  priceBlockAnalysis
}: {
  fields: StructuredFields | null | undefined;
  priceBlockAnalysis?: PriceBlockAnalysis | null | undefined;
}) {
  const hasFields = !!fields && Object.keys(fields).length > 0;
  const hasPrice = !!priceBlockAnalysis;

  if (!hasFields && !hasPrice) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Extracción estructurada</h3>
        <p className="mt-3 text-sm text-slate-600">No hay datos de extracción estructurada para este activo.</p>
      </section>
    );
  }

  const rows: Array<{ key: string; label: string; hint?: string }> = [
    { key: "campaign", label: "Campaña (opcional)" },
    { key: "dateRange", label: "Fecha o rango (opcional)" },
    { key: "brand", label: "Marca" },
    { key: "description", label: "Descripción" },
    { key: "sku", label: "SKU" },
    { key: "priceCmr", label: "Precio CMR" },
    { key: "priceRegular", label: "Precio regular" },
    { key: "priceBefore", label: "Precio antes" },
    { key: "priceMain", label: "Precio principal (candidato)" },
    { key: "priceSecondary", label: "Precio secundario (candidato)" }
  ];

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Extracción estructurada</h3>
      <p className="mt-1 text-sm text-slate-600">
        Se agrupa el OCR por bloques usando cercanía y alineación, y luego se extraen campos con heurísticas conservadoras.
      </p>

      {priceBlockAnalysis && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-900">Análisis visual del bloque principal de precio</p>
              <p className="mt-1 text-xs text-slate-600">
                Color detectado: <span className="font-semibold">{colorLabel(priceBlockAnalysis.mainBlockColor)}</span>{" "}
                {priceBlockAnalysis.mainBlockColorConfidence > 0
                  ? `(confianza ${(priceBlockAnalysis.mainBlockColorConfidence * 100).toFixed(0)}%)`
                  : ""}
              </p>
              {priceBlockAnalysis.classificationStrategy && (
                <p className="mt-1 text-xs text-slate-600">Estrategia: {priceBlockAnalysis.classificationStrategy}</p>
              )}
            </div>
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Bbox</p>
              <p className="mt-1 text-xs font-medium text-slate-800">
                {priceBlockAnalysis.mainBlockBbox ? priceBlockAnalysis.mainBlockBbox.join(", ") : "—"}
              </p>
            </div>
          </div>

          {priceBlockAnalysis.messages?.length > 0 && (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-700">
              {priceBlockAnalysis.messages.map((m, idx) => (
                <li key={idx}>{m}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {hasFields && (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {rows.map(({ key, label, hint }) => {
            const field = fields?.[key];
            const status = field?.status ?? "not_detected";
            const pill = fieldStatusToPill(status);
            const value = typeof field?.value === "string" && field.value.trim() ? field.value : "—";
            const confidence =
              typeof field?.confidence === "number" && Number.isFinite(field.confidence)
                ? `${Math.round(field.confidence * 100)}%`
                : "—";

            return (
              <article key={key} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-slate-900">{label}</h4>
                    {hint && <p className="mt-0.5 text-xs text-slate-600">{hint}</p>}
                  </div>
                  <StatusPill variant={pill.variant} label={pill.label} />
                </div>
                <p className="mt-2 break-words text-sm text-slate-800">{value}</p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-600">
                  <span>Confianza: {confidence}</span>
                  {field?.sourceBlockId ? <span>Bloque: {field.sourceBlockId}</span> : <span>Bloque: —</span>}
                  {field?.sourceRegionClassName ? (
                    <span>Región: {field.sourceRegionClassName}</span>
                  ) : (
                    <span>Región: —</span>
                  )}
                  {field?.sourceStrategy ? <span>Estrategia: {field.sourceStrategy}</span> : <span>Estrategia: —</span>}
                </div>
                {field?.message && (
                  <p className="mt-2 text-xs text-slate-600">{field.message}</p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

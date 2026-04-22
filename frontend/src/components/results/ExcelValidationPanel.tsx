"use client";

import type { ExcelValidation } from "@/types/analysis";

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

function overallToPill(status: string): { variant: PillVariant; label: string } {
  if (status === "match") return { variant: "ok", label: "Coincide" };
  if (status === "partial_match") return { variant: "warning", label: "Parcial" };
  if (status === "ambiguous") return { variant: "warning", label: "Ambiguo" };
  if (status === "not_found") return { variant: "error", label: "No encontrada" };
  if (status === "not_executed") return { variant: "na", label: "No ejecutado" };
  if (status === "not_applicable") return { variant: "na", label: "No aplica" };
  if (status === "error") return { variant: "error", label: "Error" };
  return { variant: "na", label: status || "—" };
}

function fieldStatusToText(status: string): { variant: PillVariant; label: string } {
  if (status === "match") return { variant: "ok", label: "Coincide" };
  if (status === "mismatch") return { variant: "error", label: "Diferente" };
  if (status === "not_detected") return { variant: "warning", label: "No detectado" };
  if (status === "valid_empty") return { variant: "na", label: "Vacío válido" };
  return { variant: "na", label: status || "—" };
}

const FIELD_LABELS: Record<string, string> = {
  campaign: "Campaña",
  brand: "Marca",
  description: "Descripción",
  sku: "SKU",
  priceCmr: "Precio CMR",
  priceRegular: "Precio regular",
  priceBefore: "Precio antes"
};

export function ExcelValidationPanel({ validation }: { validation: ExcelValidation | null | undefined }) {
  if (!validation) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Validación con Excel</h3>
        <p className="mt-3 text-sm text-slate-600">No se ejecutó la validación con Excel.</p>
      </section>
    );
  }

  const pill = overallToPill(validation.overallStatus);
  const messages = validation.messages ?? [];
  const fields = validation.fields ?? {};
  const fieldKeys = Object.keys(fields);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Validación con Excel</h3>
          <p className="mt-1 text-sm text-slate-600">
            Comparación opcional contra un Excel cargado por el usuario (sin romper el análisis base).
          </p>
        </div>
        <StatusPill variant={pill.variant} label={pill.label} />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Ejecución</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {validation.executed ? "Ejecutada" : "No ejecutada"}
          </p>
          <p className="mt-1 text-xs text-slate-600">
            {validation.enabled ? "Excel presente" : "Sin Excel"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Aplicabilidad</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {validation.appliesToFormat === false ? "No aplica" : validation.appliesToFormat === true ? "Aplica" : "—"}
          </p>
          <p className="mt-1 text-xs text-slate-600">Formato configurado: slideshow / mtlk.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Fila / match</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {typeof validation.matchedRowIndex === "number" ? `Fila ${validation.matchedRowIndex}` : "—"}
          </p>
          <p className="mt-1 text-xs text-slate-600">
            Estrategia: {validation.matchStrategy ? validation.matchStrategy : "—"}
          </p>
        </div>
      </div>

      {messages.length > 0 && (
        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {messages.map((m, idx) => (
            <li key={idx}>{m}</li>
          ))}
        </ul>
      )}

      {fieldKeys.length > 0 && (
        <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">
          <div className="grid grid-cols-[180px_1fr_1fr_140px] gap-0 border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
            <div>Campo</div>
            <div>Excel</div>
            <div>Detectado</div>
            <div>Estado</div>
          </div>
          {fieldKeys.map((key) => {
            const item = fields[key]!;
            const pill = fieldStatusToText(item.status);
            return (
              <div
                key={key}
                className="grid grid-cols-[180px_1fr_1fr_140px] gap-0 border-b border-slate-100 px-4 py-3 text-sm"
              >
                <div className="font-semibold text-slate-900">{FIELD_LABELS[key] ?? key}</div>
                <div className="text-slate-800">{item.expected ?? "—"}</div>
                <div className="text-slate-800">{item.detected ?? "—"}</div>
                <div>
                  <StatusPill variant={pill.variant} label={pill.label} />
                </div>
                {item.message && (
                  <div className="col-span-4 mt-2 text-xs text-slate-600">{item.message}</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}


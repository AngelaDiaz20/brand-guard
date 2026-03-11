import type { LayoutValidation } from "@/types/analysis";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-semibold ${
        ok ? "bg-emerald-200 text-emerald-800" : "bg-red-200 text-red-800"
      }`}
    >
      {label}
    </span>
  );
}

function Row({
  title,
  description,
  ok,
  okLabel = "OK",
  failLabel = "ERROR"
}: {
  title: string;
  description: string;
  ok: boolean;
  okLabel?: string;
  failLabel?: string;
}) {
  return (
    <article className={`rounded-xl border p-4 ${ok ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
          <p className="mt-1 text-xs text-slate-600">{description}</p>
        </div>
        <StatusPill ok={ok} label={ok ? okLabel : failLabel} />
      </div>
    </article>
  );
}

export function LayoutValidationPanel({ layout }: { layout: LayoutValidation | null }) {
  if (!layout) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Cumplimiento de layout</h3>
        <p className="mt-3 text-sm text-slate-600">
          No hay datos de validación de layout para este activo.
        </p>
      </section>
    );
  }

  const pieceLabel =
    layout.pieceType === "1:1" ? "1:1 (Cuadrado)" : layout.pieceType === "ST" ? "ST (Story)" : "No reconocido";

  const containerOk = !layout.logoContainerDetected || layout.logoContainerSizeValid;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Cumplimiento de layout</h3>
          <p className="mt-1 text-sm text-slate-600">Formato detectado: {pieceLabel}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">Puntaje</p>
          <p className="text-2xl font-semibold text-slate-900">{layout.layoutScore}%</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Row
          title="Logo detectado"
          description="Se detecta el ícono de casa mediante template matching."
          ok={layout.logoDetected}
        />
        <Row
          title="Logo dentro del área segura"
          description="El logo debe quedar completamente dentro del área segura."
          ok={layout.logoInsideSafeArea}
        />
        <Row
          title="Tamaño del logo correcto"
          description="Tolerancia permitida: ±10% sobre el tamaño oficial."
          ok={layout.logoSizeValid}
        />
        <Row
          title="Posición del logo correcta"
          description="El logo debe aparecer en la zona superior derecha."
          ok={layout.logoPositionValid}
        />
        <Row
          title="Contenedor del logo (opcional)"
          description={
            layout.logoContainerDetected
              ? "Se detectó contenedor: se valida su tamaño (±8%)."
              : "No se detectó contenedor; el activo sigue siendo válido."
          }
          ok={containerOk}
          okLabel={layout.logoContainerDetected ? "OK" : "NO APLICA"}
          failLabel="ERROR"
        />
      </div>
    </section>
  );
}


import type { LayoutValidation } from "@/types/analysis";

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

  return (
    <span className={`rounded-full px-2 py-1 text-xs font-semibold ${styles}`}>
      {label}
    </span>
  );
}

function Row({
  title,
  description,
  status,
  okLabel = "OK",
  failLabel = "ERROR",
  warnLabel = "ADVERTENCIA",
  naLabel = "NO APLICA"
}: {
  title: string;
  description: string;
  status: PillVariant;
  okLabel?: string;
  failLabel?: string;
  warnLabel?: string;
  naLabel?: string;
}) {
  const cardStyles =
    status === "ok"
      ? "border-emerald-200 bg-emerald-50"
      : status === "warning"
        ? "border-amber-200 bg-amber-50"
        : status === "na"
          ? "border-slate-200 bg-slate-50"
          : "border-red-200 bg-red-50";

  const pillLabel =
    status === "ok" ? okLabel : status === "warning" ? warnLabel : status === "na" ? naLabel : failLabel;

  return (
    <article className={`rounded-xl border p-4 ${cardStyles}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
          <p className="mt-1 text-xs text-slate-600">{description}</p>
        </div>
        <StatusPill variant={status} label={pillLabel} />
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

  const logoDetectionStatus =
    layout.logoValidation?.logoDetection.status ?? (layout.logoDetected ? "ok" : "warning");
  const logoMessage =
    layout.logoValidation?.logoDetection.message ??
    (layout.logoDetected ? "Logo detectado." : "No se detectó logo en la pieza.");

  const hasLogo = logoDetectionStatus === "ok";

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
          description={
            hasLogo
              ? "Se detectó el ícono de casa mediante template matching."
              : `${logoMessage} La ausencia del logo no invalida automáticamente este activo.`
          }
          status={hasLogo ? "ok" : "warning"}
        />
        <Row
          title="Logo dentro del área segura"
          description={
            hasLogo
              ? "El logo debe quedar dentro del área segura."
              : "No evaluado, porque no hubo detección."
          }
          status={!hasLogo ? "na" : layout.logoInsideSafeArea ? "ok" : "error"}
        />
        <Row
          title="Tamaño del logo correcto"
          description={
            hasLogo
              ? "Tolerancia permitida: ±10% sobre el tamaño oficial."
              : "No evaluado, porque no hubo detección."
          }
          status={!hasLogo ? "na" : layout.logoSizeValid ? "ok" : "error"}
        />
        <Row
          title="Posición del logo correcta"
          description={
            hasLogo
              ? "Tolerancia permitida: ±40 px sobre la posición oficial."
              : "No evaluado, porque no hubo detección."
          }
          status={!hasLogo ? "na" : layout.logoPositionValid ? "ok" : "error"}
        />
        <Row
          title="Contenedor del logo válido"
          description={
            !hasLogo
              ? "Sin logo detectado: no se valida contenedor."
              : layout.logoContainerDetected
                ? "Se detectó contenedor: se valida su tamaño (±10%)."
                : "No se detectó contenedor; el activo sigue siendo válido."
          }
          status={
            !hasLogo
              ? "na"
              : layout.logoContainerDetected
                ? layout.logoContainerSizeValid
                  ? "ok"
                  : "error"
                : "na"
          }
        />
        <Row
          title="Texto dentro del área segura"
          description="Todos los bloques de texto detectados por OCR deben quedar dentro del área segura."
          status={layout.textInsideSafeArea ? "ok" : "error"}
        />
      </div>
    </section>
  );
}

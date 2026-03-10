import Layout from "@/components/Layout";
import { SectionCard } from "@/components/ui/SectionCard";
import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: string;
  delta?: string;
  hint?: string;
  icon: ReactNode;
};

function MetricCard({ label, value, delta, hint, icon }: MetricCardProps) {
  return (
    <SectionCard className="relative overflow-hidden p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
            {label}
          </p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
          {(delta || hint) && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {delta && (
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                  {delta}
                </span>
              )}
              {hint && <span className="text-xs text-slate-500">{hint}</span>}
            </div>
          )}
        </div>

        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-900 text-white shadow-sm">
          {icon}
        </div>
      </div>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 -top-24 h-56 w-56 rounded-full bg-[radial-gradient(circle_at_center,rgba(15,23,42,0.12),transparent_62%)]"
      />
    </SectionCard>
  );
}

function ChartPlaceholder({
  title,
  subtitle
}: {
  title: string;
  subtitle: string;
}) {
  return (
    <SectionCard className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
          Marcador
        </span>
      </div>

      <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-end gap-2">
          {[28, 45, 36, 62, 54, 70, 60, 78, 66, 82, 74, 88].map((height, index) => (
            <div
              key={index}
              className="flex-1 rounded-lg bg-gradient-to-b from-slate-900 to-slate-700/80"
              style={{ height: `${height}px` }}
            />
          ))}
        </div>
        <div className="mt-4 h-px w-full bg-slate-200" />
        <p className="mt-3 text-xs text-slate-500">
          Conecta datos reales para mostrar tendencia.
        </p>
      </div>
    </SectionCard>
  );
}

export default function DashboardPage() {
  const mock = {
    totalImages: 1842,
    ocrAccuracyAvg: 92.4,
    brandComplianceScore: 86.1,
    imagesWithErrors: 47,
    lastAnalysisDate: "2026-03-10 09:12 (America/Bogota)"
  };

  const metrics: MetricCardProps[] = [
    {
      label: "Total de imagenes analizadas",
      value: mock.totalImages.toLocaleString("en-US"),
      delta: "+8.2%",
      hint: "vs. ultimos 7 dias",
      icon: (
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6.75 7.5h10.5M6.75 12h10.5M6.75 16.5h10.5"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5.25 4.5h13.5A2.25 2.25 0 0 1 21 6.75v10.5A2.25 2.25 0 0 1 18.75 19.5H5.25A2.25 2.25 0 0 1 3 17.25V6.75A2.25 2.25 0 0 1 5.25 4.5Z"
          />
        </svg>
      )
    },
    {
      label: "Promedio de precision OCR",
      value: `${mock.ocrAccuracyAvg.toFixed(1)}%`,
      delta: "+0.6%",
      hint: "ultimos 30 dias",
      icon: (
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.5 12.5 11 15l5-6" />
        </svg>
      )
    },
    {
      label: "Puntaje de cumplimiento de marca",
      value: `${mock.brandComplianceScore.toFixed(1)}%`,
      hint: "alineacion a lineamientos",
      icon: (
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 2.25 20.25 6v6c0 5.25-3.5 9.75-8.25 10.5C7.25 21.75 3.75 17.25 3.75 12V6L12 2.25Z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.5 11 14.5 15.5 10" />
        </svg>
      )
    },
    {
      label: "Imagenes con errores",
      value: mock.imagesWithErrors.toLocaleString("en-US"),
      hint: "requiere revision",
      icon: (
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v4m0 4h.01M10.29 3.86l-8.1 14.04A1.5 1.5 0 0 0 3.5 20.25h17a1.5 1.5 0 0 0 1.31-2.35l-8.1-14.04a1.5 1.5 0 0 0-2.62 0Z"
          />
        </svg>
      )
    },
    {
      label: "Fecha del ultimo analisis",
      value: "10 Mar 2026",
      hint: mock.lastAnalysisDate,
      icon: (
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M7.5 3v2.25M16.5 3v2.25M4.5 7.5h15"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6.75 5.25h10.5A2.25 2.25 0 0 1 19.5 7.5v11.25A2.25 2.25 0 0 1 17.25 21H6.75A2.25 2.25 0 0 1 4.5 18.75V7.5A2.25 2.25 0 0 1 6.75 5.25Z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 11h4M8 14.5h8" />
        </svg>
      )
    }
  ];

  const recentActivity = [
    {
      id: "AN-10492",
      file: "sodimac_banner_2026-03-10.jpg",
      status: "Completado",
      score: "88%",
      time: "Hoy, 09:12"
    },
    {
      id: "AN-10491",
      file: "promo_hogar_mensual.png",
      status: "Completado",
      score: "83%",
      time: "Hoy, 08:54"
    },
    {
      id: "AN-10490",
      file: "flyer_temporada_verano.tiff",
      status: "Error",
      score: "--",
      time: "Ayer, 18:31"
    },
    {
      id: "AN-10489",
      file: "packshot_producto_0310.webp",
      status: "Completado",
      score: "91%",
      time: "Ayer, 16:02"
    }
  ] as const;

  return (
    <Layout title="Panel de control">
      <div className="space-y-6">
        <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                Plataforma de analisis de imagenes
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">
                Metricas del sistema
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Resumen de analitica simulada para OCR y cumplimiento.
              </p>
            </div>

            <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
              <button
                type="button"
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
              >
                Ultimos 7 dias
              </button>
              <button
                type="button"
                className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800"
              >
                Exportar
              </button>
            </div>
          </div>

          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-28 -top-28 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_center,rgba(15,23,42,0.12),transparent_62%)]"
          />
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -bottom-32 -left-32 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_center,rgba(15,23,42,0.10),transparent_62%)]"
          />
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ChartPlaceholder
              title="Rendimiento de analisis"
              subtitle="Imagenes analizadas por dia (simulado)"
            />
          </div>
          <div className="lg:col-span-1">
            <SectionCard className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    Desglose de calidad
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Senales de OCR y cumplimiento (simulado)
                  </p>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                  Marcador
                </span>
              </div>

              <div className="mt-5 space-y-3">
                {[
                  { label: "Precision OCR", value: 92 },
                  { label: "Cumplimiento", value: 86 },
                  { label: "Tasa de error", value: 4 }
                ].map((row) => (
                  <div key={row.label}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-700">{row.label}</span>
                      <span className="text-slate-500">{row.value}%</span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-slate-900"
                        style={{ width: `${row.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">
                  Agrega distribuciones reales para reemplazar estos marcadores.
                </p>
              </div>
            </SectionCard>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <SectionCard className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Actividad reciente</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Ultimos analisis de imagen (simulado)
                  </p>
                </div>
                <button
                  type="button"
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
                >
                  Ver todo
                </button>
              </div>

              <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
                <ul className="divide-y divide-slate-200">
                  {recentActivity.map((item) => {
                    const isError = item.status === "Error";
                    return (
                      <li key={item.id} className="bg-white px-4 py-4 sm:px-5">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900">
                              {item.file}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {item.id} • {item.time}
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <span
                              className={[
                                "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold",
                                isError
                                  ? "bg-rose-50 text-rose-700"
                                  : "bg-emerald-50 text-emerald-700"
                              ].join(" ")}
                            >
                              {item.status}
                            </span>
                            <span className="text-sm font-semibold text-slate-900">
                              {item.score}
                            </span>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </SectionCard>
          </div>

          <div className="lg:col-span-1">
            <SectionCard className="p-5">
              <p className="text-sm font-semibold text-slate-900">Notas</p>
              <p className="mt-1 text-xs text-slate-500">
                Este tablero usa solo datos simulados.
              </p>

              <div className="mt-5 space-y-3">
                {[
                  { label: "Backend", value: "FastAPI (conectado en otra parte)" },
                  { label: "Pipeline OCR", value: "No conectado aqui" },
                  { label: "Fuente de datos", value: "Constantes simuladas" }
                ].map((row) => (
                  <div
                    key={row.label}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                      {row.label}
                    </p>
                    <p className="mt-1 text-sm font-medium text-slate-900">{row.value}</p>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        </section>
      </div>
    </Layout>
  );
}

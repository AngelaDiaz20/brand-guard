"use client";

import { useEffect, useState } from "react";
import Image from "next/image";

const ANALYZE_ENDPOINT = "http://127.0.0.1:8000/analyze";

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const applySelectedFile = (file: File) => {
    setSelectedFile(file);
    setResult(null);
    setLoading(false);
    setPreviewUrl((previousUrl) => {
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
      return URL.createObjectURL(file);
    });
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !file.type.startsWith("image/")) {
      return;
    }
    applySelectedFile(file);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(ANALYZE_ENDPOINT, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({}));
        const detail =
          typeof errorPayload?.detail === "string"
            ? errorPayload.detail
            : "Error while analyzing image.";
        throw new Error(detail);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Analyze request failed:", error);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setSelectedFile(null);
    setLoading(false);
    setPreviewUrl((previousUrl) => {
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
      return null;
    });
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">SODIMAC</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Análisis de imagen</h1>
      </header>

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Entrada</h2>
          <p className="mt-1 text-sm text-slate-500">
            Seleccione o suelte una imagen
          </p>

          <label
            className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center transition hover:border-slate-400"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const file = event.dataTransfer.files?.[0];
              if (!file || !file.type.startsWith("image/")) {
                return;
              }
              applySelectedFile(file);
            }}
          >
            <span className="text-sm font-medium text-slate-700">Arrastrar y soltar imagen</span>
            <span className="mt-1 text-xs text-slate-500">o haga clic para elegir el archivo</span>
            <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
          </label>

          {selectedFile && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="truncate text-sm font-medium text-slate-900">{selectedFile.name}</p>
              <p className="mt-1 text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(2)} KB</p>
            </div>
          )}

          <div className="mt-4 grid gap-2">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
              className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analizando..." : "Analizar"}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Nuevo analisis
            </button>
          </div>

          {previewUrl && (
            <div className="mt-5 rounded-xl bg-gray-100 p-4 shadow-inner">
              <div className="rounded-xl bg-white p-3 shadow-md">
                <Image
                  src={previewUrl}
                  alt="Selected preview"
                  width={1600}
                  height={900}
                  unoptimized
                  className="h-auto max-h-[500px] w-full rounded-lg object-contain"
                />
              </div>
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {!loading && !result && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
              Aún no hay análisis. Sube una imagen y haz clic en "Analizar".
            </div>
          )}

          {loading && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-8 text-center text-sm font-medium text-blue-700">
              Analizando...
            </div>
          )}

          {result && (
            <div className="space-y-6">
              <section className="rounded-xl border border-slate-200 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Metadata</h3>
                <dl className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-slate-500">Nombre</dt>
                    <dd className="font-medium">{result?.meta?.filename ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Formato</dt>
                    <dd className="font-medium">{result?.meta?.format ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Resolucion</dt>
                    <dd className="font-medium">
                      {result?.meta?.width ?? "-"} x {result?.meta?.height ?? "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Radio aspecto</dt>
                    <dd className="font-medium">{result?.meta?.aspectRatio ?? "-"}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Tamaño</dt>
                    <dd className="font-medium">
                      {typeof result?.meta?.fileSizeKb === "number"
                        ? `${result.meta.fileSizeKb.toFixed(2)} KB`
                        : "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-slate-500">Modo de color</dt>
                    <dd className="font-medium">{result?.meta?.colorMode ?? "-"}</dd>
                  </div>
                </dl>
              </section>

              <section className="rounded-xl border border-slate-200 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Technical Validation
                </h3>
                <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                  {[
                    { key: "formatAllowed", label: "Format allowed" },
                    { key: "dimensionsValid", label: "Dimensions valid" },
                    { key: "fileSizeValid", label: "File size valid" }
                  ].map((item) => {
                    const ok = Boolean(result?.technicalValidation?.[item.key]);
                    return (
                      <div
                        key={item.key}
                        className={`rounded-lg border px-3 py-2 ${
                          ok
                            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "border-red-200 bg-red-50 text-red-700"
                        }`}
                      >
                        <p className="text-xs uppercase tracking-wide">{item.label}</p>
                        <p className="mt-1 text-sm font-semibold">{ok ? "OK" : "ERROR"}</p>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="rounded-xl border border-slate-200 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">
                  Dominant Colors
                </h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {(result?.visualAnalysis?.dominantColors ??
                    result?.colorAnalysis?.dominantColors ??
                    []
                  ).map((color: { hex: string; percentage: number }) => (
                    <div key={`${color.hex}-${color.percentage}`} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div
                        className="h-10 w-10 rounded-md border border-slate-200"
                        style={{ backgroundColor: color.hex }}
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-900">{color.hex}</p>
                        <p className="text-xs text-slate-500">
                          {typeof color.percentage === "number" ? color.percentage.toFixed(1) : "0.0"}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-slate-200 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">OCR</h3>
                <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                  {result?.ocr?.fullText || "No text detected."}
                </p>
                <div className="mt-3 space-y-2">
                  {(result?.ocr?.words ?? []).map(
                    (
                      word: { text: string; confidence: number; box: [number, number, number, number] },
                      index: number
                    ) => (
                      <div
                        key={`${word.text}-${index}`}
                        className="rounded-lg border border-slate-200 bg-white p-3 text-sm"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium text-slate-900">{word.text}</span>
                          <span className="text-xs text-slate-500">
                            confidence: {Number(word.confidence ?? 0).toFixed(2)}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          box: [{(word.box ?? []).join(", ")}]
                        </p>
                      </div>
                    )
                  )}
                </div>
              </section>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

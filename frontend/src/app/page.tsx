"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ProgressScreen } from "@/components/analysis/ProgressScreen";
import { ImagePreview } from "@/components/preview/ImagePreview";
import { ResultsScreen } from "@/components/results/ResultsScreen";
import { UploadArea } from "@/components/upload/UploadArea";
import { analyzeImage } from "@/lib/api";
import type { AnalyzeResponse, AppStatus } from "@/types/analysis";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Ocurrio un error inesperado durante el analisis.";
}

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<AppStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const tickerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isBusy = status === "uploading" || status === "analyzing";

  const progressPhase = useMemo(() => {
    if (status === "uploading") {
      return "uploading" as const;
    }

    return "analyzing" as const;
  }, [status]);

  const stopTicker = () => {
    if (!tickerRef.current) {
      return;
    }

    clearInterval(tickerRef.current);
    tickerRef.current = null;
  };

  useEffect(() => {
    return () => {
      if (tickerRef.current) {
        clearInterval(tickerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const resetFlow = () => {
    stopTicker();
    setStatus("idle");
    setProgress(0);
    setResult(null);
    setErrorMessage(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      return;
    }

    resetFlow();
    setStatus("uploading");
    setProgress(5);

    tickerRef.current = setInterval(() => {
      setProgress((current) => {
        if (current >= 95) {
          return current;
        }
        return current + 2;
      });
    }, 280);

    try {
      const response = await analyzeImage(selectedFile, (uploadPercent) => {
        setProgress((current) => {
          const uploadProgress = Math.min(75, Math.round(uploadPercent * 0.75));
          return Math.max(current, uploadProgress);
        });

        if (uploadPercent >= 100) {
          setStatus("analyzing");
        }
      });

      setStatus("analyzing");
      setProgress((current) => Math.max(current, 96));

      setResult(response);
      setProgress(100);
      setStatus("success");
    } catch (error) {
      setStatus("error");
      setErrorMessage(getErrorMessage(error));
    } finally {
      stopTicker();
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-6 px-4 py-10 sm:px-6 lg:px-8">
      <header>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Analizador Técnico de Imágenes</h1>
      </header>

      <UploadArea
        selectedFile={selectedFile}
        isBusy={isBusy}
        onFileSelected={(file) => {
          setPreviewUrl(URL.createObjectURL(file));
          setSelectedFile(file);
          setResult(null);
          setErrorMessage(null);
          setStatus("idle");
          setProgress(0);
        }}
        onAnalyze={handleAnalyze}
      />

      {previewUrl && <ImagePreview imageUrl={previewUrl} />}

      {isBusy && <ProgressScreen progress={progress} fileName={selectedFile?.name} phase={progressPhase} />}

      {status === "error" && errorMessage && (
        <section className="rounded-2xl border border-red-200 bg-red-50 p-4">
          <h2 className="text-sm font-semibold text-red-800">Error de analisis</h2>
          <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
        </section>
      )}

      {status === "success" && result && (
        <>
          <ResultsScreen result={result} />
          <button
            type="button"
            onClick={resetFlow}
            className="self-start rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Nuevo análisis
          </button>
        </>
      )}
    </main>
  );
}

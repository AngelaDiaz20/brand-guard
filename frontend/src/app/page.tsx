"use client";

import { useEffect, useState } from "react";

import { ImagePreview } from "@/components/preview/ImagePreview";
import { ResultsScreen } from "@/components/results/ResultsScreen";
import { UploadArea } from "@/components/upload/UploadArea";
import { analyzeImage } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/analysis";
import type { UploadFileType } from "@/types/upload";
import { getUploadFileType } from "@/types/upload";

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileType, setSelectedFileType] = useState<UploadFileType | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const applySelectedFile = (file: File, fileType: UploadFileType) => {
    setSelectedFile(file);
    setSelectedFileType(fileType);
    setResult(null);
    setLoading(false);
    setErrorMessage(null);
    setPreviewUrl((previousUrl) => {
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
      return URL.createObjectURL(file);
    });
  };

  const handleFileSelected = (file: File) => {
    const fileType = getUploadFileType(file);
    if (!fileType) {
      return;
    }
    applySelectedFile(file, fileType);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      return;
    }

    setResult(null);
    setLoading(true);
    setErrorMessage(null);

    try {
      const data = await analyzeImage(selectedFile);
      setResult(data);
    } catch (error) {
      console.error("Analyze request failed:", error);
      setResult(null);
      setErrorMessage("No se pudo analizar la imagen.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setSelectedFile(null);
    setSelectedFileType(null);
    setLoading(false);
    setErrorMessage(null);
    setPreviewUrl((previousUrl) => {
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
      return null;
    });
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">SODIMAC</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Análisis de archivo</h1>
      </header> */}

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="space-y-4">
          <UploadArea
            selectedFile={selectedFile}
            isBusy={loading}
            onFileSelected={handleFileSelected}
            onAnalyze={handleAnalyze}
          />

          {previewUrl && selectedFileType && (
            <ImagePreview fileUrl={previewUrl} fileType={selectedFileType} result={result} />
          )}

          <button
            type="button"
            onClick={handleReset}
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Nuevo análisis
          </button>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {!loading && !result && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
              Aún no hay análisis. Sube una imagen y haz clic en Analizar.
            </div>
          )}

          {loading && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-8 text-center text-sm font-medium text-blue-700">
              Analizando...
            </div>
          )}

          {errorMessage && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          {result && <ResultsScreen data={result} />}
        </section>
      </div>
    </main>
  );
}

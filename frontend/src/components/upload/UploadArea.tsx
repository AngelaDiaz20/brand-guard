"use client";

import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { SectionCard } from "@/components/ui/SectionCard";

interface UploadAreaProps {
  selectedFile: File | null;
  isBusy: boolean;
  onFileSelected: (file: File) => void;
  onAnalyze: () => void;
}

export function UploadArea({
  selectedFile,
  isBusy,
  onFileSelected,
  onAnalyze
}: UploadAreaProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const pickFile = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelected(file);
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];
    if (!file || !file.type.startsWith("image/")) {
      return;
    }

    onFileSelected(file);
  };

  return (
    <SectionCard>
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Cargar imagen</h2>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`rounded-xl border-2 border-dashed p-8 text-center transition ${
          isDragging
            ? "border-brand-500 bg-brand-50"
            : "border-slate-300 bg-slate-50 hover:border-slate-400"
        }`}
      >
        <p className="text-sm font-medium text-slate-700">Drag & Drop de imagen</p>
        <p className="mt-1 text-xs text-slate-500">PNG, JPG, WEBP, TIFF, etc.</p>

        <button
          type="button"
          onClick={pickFile}
          disabled={isBusy}
          className="mt-5 rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Seleccionar archivo
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleInputChange}
        />
      </div>

      {selectedFile && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-sm font-medium text-slate-800">{selectedFile.name}</p>
          <p className="text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(2)} KB</p>
        </div>
      )}

      <button
        type="button"
        disabled={!selectedFile || isBusy}
        onClick={onAnalyze}
        className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Analizar imagen
      </button>
    </SectionCard>
  );
}

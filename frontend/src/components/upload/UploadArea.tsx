"use client";

import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { SectionCard } from "@/components/ui/SectionCard";
import { getUploadFileType, UPLOAD_ACCEPT } from "@/types/upload";
import type { AnalysisItem } from "@/types/analysisBatch";

interface UploadAreaProps {
  items: AnalysisItem[];
  isBusy: boolean;
  onFilesSelected: (files: File[]) => void;
  onRemoveItem: (id: string) => void;
  onClearSelection: () => void;
  onAnalyze: () => void;
}

export function UploadArea({
  items,
  isBusy,
  onFilesSelected,
  onRemoveItem,
  onClearSelection,
  onAnalyze
}: UploadAreaProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const pickFile = () => {
    fileInputRef.current?.click();
  };

  const addFilesFromList = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) {
      return;
    }

    const files = Array.from(fileList).filter((file) => !!getUploadFileType(file));
    if (files.length === 0) {
      return;
    }

    onFilesSelected(files);
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    addFilesFromList(event.target.files);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    if (isBusy) {
      return;
    }

    addFilesFromList(event.dataTransfer.files);
  };

  const anySelected = items.length > 0;
  const isMulti = items.length > 1;
  const canAnalyze = anySelected && !isBusy;

  return (
    <SectionCard>
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-slate-900">Cargar imágenes</h2>
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
        <p className="text-sm font-medium text-slate-700">Arrastra tus imágenes aquí</p>
        <p className="mt-1 text-xs text-slate-500">JPG, JPEG, PNG o PDF.</p>

        <button
          type="button"
          onClick={pickFile}
          disabled={isBusy}
          className="mt-5 rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Seleccionar imágenes
        </button>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={UPLOAD_ACCEPT}
          className="hidden"
          onChange={handleInputChange}
        />
      </div>

      {anySelected && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-800">
              Selección ({items.length})
            </p>
            <button
              type="button"
              disabled={isBusy}
              onClick={onClearSelection}
              className="text-xs font-semibold text-slate-600 underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-60"
            >
              Limpiar selección
            </button>
          </div>

          <div className="max-h-56 space-y-2 overflow-auto pr-1">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-2"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="h-10 w-10 shrink-0 overflow-hidden rounded-md border border-slate-200 bg-slate-50">
                    {item.input.fileType === "image" ? (
                      <img
                        src={item.input.previewUrl}
                        alt={`Miniatura de ${item.input.fileName}`}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="grid h-full w-full place-items-center text-[10px] font-semibold text-slate-500">
                        PDF
                      </div>
                    )}
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold text-slate-800">{item.input.fileName}</p>
                    <p className="text-[11px] text-slate-500">
                      {(item.input.file?.size ?? 0) > 0
                        ? `${((item.input.file!.size ?? 0) / 1024).toFixed(2)} KB`
                        : "—"}
                      {" · "}
                      {item.state === "pendiente"
                        ? "Pendiente"
                        : item.state === "subiendo"
                          ? `Subiendo${typeof item.progressPercent === "number" ? ` ${item.progressPercent}%` : ""}`
                          : item.state === "analizando"
                            ? "Analizando"
                            : item.state === "listo"
                              ? "Completado"
                              : "Error"}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  disabled={isBusy || item.state === "subiendo" || item.state === "analizando"}
                  onClick={() => onRemoveItem(item.id)}
                  className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Eliminar
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        disabled={!canAnalyze}
        onClick={onAnalyze}
        className="mt-5 w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isMulti ? "Analizar lote" : "Analizar imagen"}
      </button>
    </SectionCard>
  );
}

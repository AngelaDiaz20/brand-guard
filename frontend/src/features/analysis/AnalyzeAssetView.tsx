"use client";

import { useMemo } from "react";

import { BatchResultsView } from "@/components/analysis/batch/BatchResultsView";
import { ImagePreview } from "@/components/preview/ImagePreview";
import { UploadArea } from "@/components/upload/UploadArea";
import { useBatchImageAnalysis } from "@/features/analysis/useBatchImageAnalysis";

export function AnalyzeAssetView() {
  const {
    items,
    isBusy,
    errorMessage,
    infoMessage,
    excelFile,
    setExcelFile,
    pieceFormat,
    setPieceFormat,
    addFiles,
    removeItem,
    clearBatch,
    analyzeBatch,
    retryItem
  } =
    useBatchImageAnalysis({ maxConcurrency: 3 });

  const singleItem = items.length === 1 ? items[0] : null;
  const isMulti = items.length > 1;
  const canClear = items.length > 0;
  const previewResult = useMemo(() => (singleItem?.state === "listo" ? singleItem.output : null), [singleItem]);

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <div className="space-y-4">
        <UploadArea
          items={items}
          isBusy={isBusy}
          onFilesSelected={addFiles}
          onRemoveItem={removeItem}
          onClearSelection={clearBatch}
          onAnalyze={analyzeBatch}
          excelFile={excelFile}
          pieceFormat={pieceFormat}
          onExcelSelected={setExcelFile}
          onPieceFormatChanged={setPieceFormat}
        />

        {singleItem && (
          <ImagePreview
            fileUrl={singleItem.input.previewUrl}
            fileType={singleItem.input.fileType}
            result={previewResult}
          />
        )}

        <button
          type="button"
          onClick={clearBatch}
          disabled={isBusy || !canClear}
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isMulti ? "Limpiar lote" : "Limpiar selección"}
        </button>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {infoMessage && (
          <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {infoMessage}
          </div>
        )}

        {errorMessage && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        <BatchResultsView
          items={items}
          onRetryItem={retryItem}
          isBusy={isBusy}
        />
      </section>
    </div>
  );
}

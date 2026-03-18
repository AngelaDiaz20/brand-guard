"use client";

import type { AnalyzeResponse } from "@/types/analysis";
import type { UploadFileType } from "@/types/upload";
import { calculateScore, getValidationItems } from "@/utils/analysis";

import { ImagePreview } from "@/components/preview/ImagePreview";
import { ColorPalette } from "@/components/results/ColorPalette";
import { LayoutValidationPanel } from "@/components/results/LayoutValidationPanel";
import { MetadataPanel } from "@/components/results/MetadataPanel";
import { OCRPanel } from "@/components/results/OCRPanel";
import { ValidationCard } from "@/components/results/ValidationCard";
import { DisclosureSection } from "@/components/ui/DisclosureSection";
import { ScoreSummary } from "@/components/analysis/batch/ScoreSummary";

interface AnalysisDetailPanelProps {
  result: AnalyzeResponse;
  preview?: {
    fileUrl: string;
    fileType: UploadFileType;
  };
}

export function AnalysisDetailPanel({ result, preview }: AnalysisDetailPanelProps) {
  const validationItems = getValidationItems(result.technicalValidation);
  const passed = validationItems.filter((item) => item.ok).length;
  const technicalScore = calculateScore(result.technicalValidation);
  const layoutScore = result.layoutValidation ? Math.round(result.layoutValidation.layoutScore ?? 0) : null;
  const ocrScore = typeof result.ocr?.score === "number" ? Math.round(result.ocr.score) : null;
  const dominantColors = result.colorAnalysis?.dominantColors ?? [];

  return (
    <div className="grid gap-4">
      <DisclosureSection
        title="Resumen"
        defaultOpen
        badge={
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700">
            {passed}/{validationItems.length} técnicas
          </span>
        }
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <ScoreSummary title="Técnico" score={technicalScore} subtitle="Validaciones técnicas" />
          {layoutScore !== null && <ScoreSummary title="Layout" score={layoutScore} subtitle="Área segura, logo y contenedor" />}
          {ocrScore !== null && <ScoreSummary title="OCR" score={ocrScore} subtitle="Confianza y correcciones" />}
        </div>
      </DisclosureSection>

      {preview && (
        <DisclosureSection title="Vista previa con overlays" defaultOpen={false}>
          <ImagePreview fileUrl={preview.fileUrl} fileType={preview.fileType} result={result} />
        </DisclosureSection>
      )}

      <DisclosureSection title="Metadatos" defaultOpen={false}>
        <MetadataPanel metadata={result.meta} />
      </DisclosureSection>

      {dominantColors.length > 0 && (
        <DisclosureSection title="Colores dominantes" defaultOpen={false}>
          <ColorPalette dominantColors={dominantColors} />
        </DisclosureSection>
      )}

      <DisclosureSection title="Validaciones técnicas" defaultOpen={false}>
        <div className="grid gap-3 md:grid-cols-3">
          {validationItems.map((item) => (
            <ValidationCard key={item.key} item={item} />
          ))}
        </div>
      </DisclosureSection>

      <DisclosureSection title="OCR" defaultOpen={false}>
        <OCRPanel ocr={result.ocr ?? null} />
      </DisclosureSection>

      <DisclosureSection title="Validación de layout" defaultOpen={false}>
        <LayoutValidationPanel layout={result.layoutValidation ?? null} />
      </DisclosureSection>
    </div>
  );
}

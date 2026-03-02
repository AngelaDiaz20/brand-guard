import type { AnalyzeResponse } from "@/types/analysis";
import { calculateScore, getValidationItems } from "@/utils/analysis";

import { OCRPanel } from "@/components/results/OCRPanel";
import { ColorPalette } from "@/components/results/ColorPalette";
import { MetadataPanel } from "@/components/results/MetadataPanel";
import { ScoreCard } from "@/components/results/ScoreCard";
import { ValidationCard } from "@/components/results/ValidationCard";

interface ResultsScreenProps {
  data: AnalyzeResponse;
}

export function ResultsScreen({ data }: ResultsScreenProps) {
  const validationItems = getValidationItems(data.technicalValidation);
  const passed = validationItems.filter((item) => item.ok).length;
  const score = calculateScore(data.technicalValidation);
  const dominantColors = data.colorAnalysis?.dominantColors ?? []; 

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScoreCard score={score} passedChecks={passed} totalChecks={validationItems.length} />
      </div>

      <div className="lg:col-span-2">
        <MetadataPanel metadata={data.meta} />
      </div>

      {dominantColors.length > 0 && (
        <div className="lg:col-span-2">
          <ColorPalette dominantColors={dominantColors} />
        </div>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
        <h3 className="text-lg font-semibold text-slate-900">Validaciones técnicas</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {validationItems.map((item) => (
            <ValidationCard key={item.key} item={item} />
          ))}
        </div>
      </section>

      <div className="lg:col-span-2">
        {/* Verificación de json en render
        <pre className="lg:col-span-2 text-xs whitespace-pre-wrap">
          {JSON.stringify(data.ocr, null, 2)}
        </pre>*/}
        <OCRPanel ocr={data.ocr ?? null} />
      </div>
    </div>
  );
}
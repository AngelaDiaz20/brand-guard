import type { AnalyzeResponse } from "@/types/analysis";
import { calculateScore, getValidationItems } from "@/utils/analysis";

import { MetadataPanel } from "@/components/results/MetadataPanel";
import { ScoreCard } from "@/components/results/ScoreCard";
import { ValidationCard } from "@/components/results/ValidationCard";

interface ResultsScreenProps {
  result: AnalyzeResponse;
}

export function ResultsScreen({ result }: ResultsScreenProps) {
  const validationItems = getValidationItems(result.technicalValidation);
  const passed = validationItems.filter((item) => item.ok).length;
  const score = calculateScore(result.technicalValidation);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <MetadataPanel metadata={result.meta} />
        <ScoreCard score={score} passedChecks={passed} totalChecks={validationItems.length} />
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Validaciones tecnicas</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {validationItems.map((item) => (
            <ValidationCard key={item.key} item={item} />
          ))}
        </div>
      </section>
    </div>
  );
}

import { SectionCard } from "@/components/ui/SectionCard";

interface ScoreCardProps {
  score: number;
  passedChecks: number;
  totalChecks: number;
}

export function ScoreCard({ score, passedChecks, totalChecks }: ScoreCardProps) {
  return (
    <SectionCard className="bg-slate-900 text-white">
      <p className="text-sm font-medium text-slate-300">Score general</p>
      <div className="mt-3 flex items-end justify-between">
        <span className="text-4xl font-bold">{score}</span>
        <span className="text-base font-medium text-slate-300">/ 100</span>
      </div>
      <p className="mt-2 text-sm text-slate-300">
        {passedChecks} de {totalChecks} validaciones tecnicas aprobadas.
      </p>
    </SectionCard>
  );
}

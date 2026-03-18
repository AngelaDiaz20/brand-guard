interface ScoreSummaryProps {
  title?: string;
  score: number;
  subtitle?: string;
}

export function ScoreSummary({ title = "Puntaje", score, subtitle }: ScoreSummaryProps) {
  const safeScore = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-600">{subtitle}</p>}
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-slate-900">{Math.round(safeScore)}</p>
          <p className="-mt-1 text-xs text-slate-500">/ 100</p>
        </div>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${safeScore}%` }} />
      </div>
    </div>
  );
}

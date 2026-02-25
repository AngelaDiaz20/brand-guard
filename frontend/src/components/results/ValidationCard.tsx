import type { ValidationItem } from "@/types/analysis";

interface ValidationCardProps {
  item: ValidationItem;
}

export function ValidationCard({ item }: ValidationCardProps) {
  return (
    <article
      className={`rounded-xl border p-4 ${
        item.ok ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{item.label}</h4>
          <p className="mt-1 text-xs text-slate-600">{item.description}</p>
        </div>
        <span
          className={`rounded-full px-2 py-1 text-xs font-semibold ${
            item.ok ? "bg-emerald-200 text-emerald-800" : "bg-red-200 text-red-800"
          }`}
        >
          {item.ok ? "OK" : "ERROR"}
        </span>
      </div>
    </article>
  );
}

import type { ColorItem } from "@/types/analysis";

interface ColorPaletteProps {
  dominantColors: ColorItem[];
}

export function ColorPalette({ dominantColors }: ColorPaletteProps) {
  if (!dominantColors?.length) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Colores dominantes</h3>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {dominantColors.map((color) => (
          <article
            key={`${color.hex}-${color.percentage}`}
            className="flex items-center gap-4 rounded-xl border border-slate-200 bg-slate-50 p-3"
          >
            <div
              className="h-16 w-16 flex-none rounded-lg shadow-lg ring-1 ring-black/5"
              style={{ backgroundColor: color.hex }}
              aria-label={`Muestra de color ${color.hex}`}
            />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold uppercase tracking-wide text-slate-900">
                {color.hex}
              </p>
              <p className="text-xs text-slate-500">{color.percentage.toFixed(1)}%</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

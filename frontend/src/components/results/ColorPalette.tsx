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

    <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
      {dominantColors.slice(0, 5).map((color) => (
        <article
          key={`${color.hex}-${color.percentage}`}
          className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
        >
          <div
            className="h-36 w-full"
            style={{ backgroundColor: color.hex }}
            aria-label={`Muestra de color ${color.hex}`}
          />

          <div className="px-4 py-3 text-center">
            <p className="text-sm font-semibold text-slate-800">{color.hex}</p>
            <p className="mt-1 text-xs text-slate-500">{color.percentage.toFixed(1)}%</p>
          </div>
        </article>
      ))}
    </div>
  </section>
  );
}

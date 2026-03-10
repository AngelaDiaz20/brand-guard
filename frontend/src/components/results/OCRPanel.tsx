import type { OCRResponse } from "@/types/analysis"; // ajusta la ruta

interface OCRPanelProps {
  ocr: OCRResponse | null;
}

export function OCRPanel({ ocr }: OCRPanelProps) {
  if (!ocr) return null;

  const { rawText, correctedText, confidence } = ocr;

  const hasAny =
    rawText?.trim().length > 0 || correctedText?.trim().length > 0;

  if (!hasAny) return null;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-slate-900">Texto</h3>

        {confidence && (
          <div className="text-xs text-slate-500 text-right">
            <div>avg: {confidence.avg.toFixed(2)}</div>
            <div>min: {confidence.min.toFixed(2)}</div>
          </div>
        )}
      </div>

      {/*{rawText?.trim() && (
        <>
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Texto extraído (RAW)
          </p>
          <pre className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {rawText}
          </pre>
        </>
      )} */}

      {correctedText?.trim() && correctedText !== rawText && (
        <>
          <p className="mt-4 text-sm font-semibold text-slate-700">
            
          </p>
          <pre className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {correctedText}
          </pre>
        </>
      )}
    </section>
  );
}
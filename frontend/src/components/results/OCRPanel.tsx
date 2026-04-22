import type { OCRResponse } from "@/types/analysis"; // ajusta la ruta

interface OCRPanelProps {
  ocr: OCRResponse | null;
}

export function OCRPanel({ ocr }: OCRPanelProps) {
  if (!ocr) return null;

  const {
    rawText,
    correctedText,
    lines,
    microBlocks,
    blocks,
    regions,
    regionalOcr,
    incidentalRegionalOcr,
    yoloDetections,
    globalLines,
    globalMicroBlocks,
    globalBlocks,
  } = ocr;

  const hasAny =
    rawText?.trim().length > 0 || correctedText?.trim().length > 0;

  if (!hasAny) return null;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-slate-900">OCR</h3>

        {confidence && (
          <div className="text-xs text-slate-500 text-right">
             <div>avg: {confidence.avg.toFixed(2)}</div>
            <div>min: {confidence.min.toFixed(2)}</div>
          </div> 
        )} 
      </div> */}

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {rawText?.trim() && (
          <div>
            <p className="text-sm font-semibold text-slate-700">Texto extraído (RAW)</p>
            <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
              {rawText}
            </pre>
          </div>
        )}

        {correctedText?.trim() && (
          <div>
            <p className="text-sm font-semibold text-slate-700">Texto corregido</p>
            <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
              {correctedText}
            </pre>
          </div>
        )}
      </div>

      {Array.isArray(yoloDetections) && yoloDetections.length > 0 && (
        <details className="mt-5 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Regiones YOLO detectadas ({yoloDetections.length})
          </summary>
          <p className="mt-2 text-xs text-slate-600">
            Detección semántica previa al OCR (si está habilitada y configurada en backend).
          </p>
          <div className="mt-3 space-y-2">
            {yoloDetections.map((r) => (
              <div key={r.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold text-slate-700">
                  {r.id}
                  {r.className ? ` · ${r.className}` : ""}
                  {r.source ? ` · ${r.source}` : ""}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {r.bbox.join(", ")}
                  {typeof r.confidence === "number" ? ` · confianza: ${(r.confidence * 100).toFixed(0)}%` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(regions) && regions.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Regiones usadas para OCR ({regions.length})
          </summary>
          <p className="mt-2 text-xs text-slate-600">
            Estas regiones se usan para ejecutar OCR por recortes y evitar mezcla entre zonas visuales.
          </p>
          <div className="mt-3 space-y-2">
            {regions.map((r) => (
              <div key={r.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold text-slate-700">
                  {r.id}
                  {r.className ? ` · ${r.className}` : ""}
                  {r.kind ? ` · ${r.kind}` : ""}
                  {r.source ? ` · ${r.source}` : ""}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {r.bbox.join(", ")}
                  {typeof r.confidence === "number" ? ` · confianza: ${(r.confidence * 100).toFixed(0)}%` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(regionalOcr) && regionalOcr.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            OCR por región ({regionalOcr.length})
          </summary>
          <div className="mt-3 space-y-2">
            {regionalOcr.map((r) => (
              <div key={r.regionId} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold text-slate-700">{r.regionId}</p>
                <p className="mt-1 text-[11px] text-slate-500">bbox: {r.bbox.join(", ")}</p>
                {r.rawText?.trim() && (
                  <>
                    <p className="mt-2 text-xs font-semibold text-slate-700">RAW</p>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-2 text-xs leading-relaxed text-slate-700">
                      {r.rawText}
                    </pre>
                  </>
                )}
                {r.correctedText?.trim() && (
                  <>
                    <p className="mt-2 text-xs font-semibold text-slate-700">Corregido</p>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-2 text-xs leading-relaxed text-slate-700">
                      {r.correctedText}
                    </pre>
                  </>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(incidentalRegionalOcr) && incidentalRegionalOcr.length > 0 && (
        <details className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            OCR incidental (dentro de foto) ({incidentalRegionalOcr.length})
          </summary>
          <p className="mt-2 text-xs text-slate-700">
            Solo para depuración: texto detectado dentro de <code>product_photo_area</code>. No participa en la extracción principal.
          </p>
          <div className="mt-3 space-y-2">
            {incidentalRegionalOcr.map((r) => (
              <div key={r.regionId} className="rounded-lg border border-amber-200 bg-white p-3">
                <p className="text-xs font-semibold text-slate-700">{r.regionId}</p>
                <p className="mt-1 text-[11px] text-slate-500">bbox: {r.bbox.join(", ")}</p>
                {r.rawText?.trim() && (
                  <>
                    <p className="mt-2 text-xs font-semibold text-slate-700">RAW</p>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-amber-200 bg-white p-2 text-xs leading-relaxed text-slate-700">
                      {r.rawText}
                    </pre>
                  </>
                )}
                {r.correctedText?.trim() && (
                  <>
                    <p className="mt-2 text-xs font-semibold text-slate-700">Corregido</p>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-amber-200 bg-white p-2 text-xs leading-relaxed text-slate-700">
                      {r.correctedText}
                    </pre>
                  </>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(lines) && lines.length > 0 && (
        <details className="mt-5 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Líneas detectadas ({lines.length})
          </summary>
          <div className="mt-3 space-y-2">
            {lines.map((line) => (
              <div key={line.id ?? line.text} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold text-slate-700">{line.id ?? "línea"}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{line.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {line.bbox.join(", ")} · confianza: {(line.confidence * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(globalLines) && globalLines.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Líneas (OCR global original) ({globalLines.length})
          </summary>
          <p className="mt-2 text-xs text-slate-600">
            Referencia de depuración: salida del OCR global antes de aplicar OCR por regiones.
          </p>
          <div className="mt-3 space-y-2">
            {globalLines.map((line) => (
              <div key={line.id ?? line.text} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold text-slate-700">{line.id ?? "línea"}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{line.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {line.bbox.join(", ")} · confianza: {(line.confidence * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(microBlocks) && microBlocks.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Microbloques ({microBlocks.length})
          </summary>
          <p className="mt-2 text-xs text-slate-600">
            Agrupación estricta por macrozonas + alineación. Sirve como base para los bloques finales.
          </p>
          <div className="mt-3 space-y-2">
            {microBlocks.map((block) => (
              <div key={block.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">
                    {block.id}
                    {block.type ? ` · ${block.type}` : ""}
                    {block.zone ? ` · ${block.zone}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    confianza: {(block.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{block.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {block.bbox.join(", ")}
                  {block.lineIds?.length ? ` · líneas: ${block.lineIds.join(", ")}` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(globalMicroBlocks) && globalMicroBlocks.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Microbloques (OCR global original) ({globalMicroBlocks.length})
          </summary>
          <div className="mt-3 space-y-2">
            {globalMicroBlocks.map((block) => (
              <div key={block.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">
                    {block.id}
                    {block.type ? ` · ${block.type}` : ""}
                    {block.zone ? ` · ${block.zone}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    confianza: {(block.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{block.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {block.bbox.join(", ")}
                  {block.lineIds?.length ? ` · líneas: ${block.lineIds.join(", ")}` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(blocks) && blocks.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Bloques reconstruidos ({blocks.length})
          </summary>
          <div className="mt-3 space-y-2">
            {blocks.map((block) => (
              <div key={block.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">
                    {block.id}
                    {block.type ? ` · ${block.type}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    confianza: {(block.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{block.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {block.bbox.join(", ")}
                  {block.lineIds?.length ? ` · líneas: ${block.lineIds.join(", ")}` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {Array.isArray(globalBlocks) && globalBlocks.length > 0 && (
        <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
            Bloques (OCR global original) ({globalBlocks.length})
          </summary>
          <div className="mt-3 space-y-2">
            {globalBlocks.map((block) => (
              <div key={block.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">
                    {block.id}
                    {block.type ? ` · ${block.type}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    confianza: {(block.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{block.text}</p>
                <p className="mt-1 text-[11px] text-slate-500">
                  bbox: {block.bbox.join(", ")}
                  {block.lineIds?.length ? ` · líneas: ${block.lineIds.join(", ")}` : ""}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}

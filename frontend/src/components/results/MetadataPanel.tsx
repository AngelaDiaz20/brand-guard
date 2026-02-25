import type { Metadata } from "@/types/analysis";
import { toMegaBytes } from "@/utils/analysis";

import { SectionCard } from "@/components/ui/SectionCard";

interface MetadataPanelProps {
  metadata: Metadata;
}

export function MetadataPanel({ metadata }: MetadataPanelProps) {
  return (
    <SectionCard>
      <h3 className="text-lg font-semibold text-slate-900">Metadata basica</h3>
      <dl className="mt-4 grid grid-cols-1 gap-3 text-sm text-slate-700 sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Nombre</dt>
          <dd className="font-medium">{metadata.filename}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Formato</dt>
          <dd className="font-medium">{metadata.format}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Tamano</dt>
          <dd className="font-medium">{metadata.fileSizeKb.toFixed(2)} KB ({toMegaBytes(metadata.fileSizeKb)})</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Resolucion</dt>
          <dd className="font-medium">
            {metadata.width} x {metadata.height}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">Aspect Ratio</dt>
          <dd className="font-medium">{metadata.aspectRatio}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-500">ICC</dt>
          <dd className="font-medium">{metadata.iccProfile ?? "No disponible"}</dd>
        </div>
      </dl>
    </SectionCard>
  );
}

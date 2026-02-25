import { SectionCard } from "@/components/ui/SectionCard";

interface ProgressScreenProps {
  progress: number;
  fileName?: string;
  phase: "uploading" | "analyzing";
}

const PHASE_TEXT: Record<ProgressScreenProps["phase"], string> = {
  uploading: "Subiendo archivo al backend...",
  analyzing: "Procesando metadata y validaciones tecnicas..."
};

export function ProgressScreen({ progress, fileName, phase }: ProgressScreenProps) {
  return (
    <SectionCard>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900">Progreso de analisis</h2>
        <span className="text-sm font-semibold text-brand-700">{progress}%</span>
      </div>

      <p className="mt-1 text-sm text-slate-500">{PHASE_TEXT[phase]}</p>

      {fileName && <p className="mt-2 text-xs text-slate-500">Archivo: {fileName}</p>}

      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-brand-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </SectionCard>
  );
}

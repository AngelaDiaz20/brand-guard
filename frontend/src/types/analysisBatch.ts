import type { AnalyzeResponse } from "@/types/analysis";
import type { UploadFileType } from "@/types/upload";

export type IndicatorState = "ok" | "alerta" | "error" | "no_aplica";
export type AnalysisStatus = "ok" | "alerta" | "error";

export interface AnalysisFileRef {
  id: string;
  fileName: string;
  fileType: UploadFileType;
  previewUrl: string;
  file?: File;
}

export type AnalysisItemState = "pendiente" | "subiendo" | "analizando" | "listo" | "error";

export type AnalysisItem =
  | {
      id: string;
      input: AnalysisFileRef;
      state: "pendiente" | "subiendo" | "analizando";
      progressPercent?: number;
      startedAtMs?: number;
      finishedAtMs?: number;
      output?: undefined;
      error?: undefined;
    }
  | {
      id: string;
      input: AnalysisFileRef;
      state: "listo";
      output: AnalyzeResponse;
      startedAtMs?: number;
      finishedAtMs?: number;
      error?: undefined;
    }
  | {
      id: string;
      input: AnalysisFileRef;
      state: "error";
      output?: undefined;
      error: string;
      startedAtMs?: number;
      finishedAtMs?: number;
    };

export interface AnalysisCardIndicator {
  key: string;
  label: string;
  state: IndicatorState;
}

export interface AnalysisCardData {
  id: string;
  fileName: string;
  format: string;
  pieceType: string | null;
  scoreGeneral: number;
  statusGeneral: AnalysisStatus;
  indicators: AnalysisCardIndicator[];
  previewUrl: string;
  fileType: UploadFileType;
  disabled?: boolean;
}

export interface BatchSummary {
  total: number;
  pendientes: number;
  enProceso: number;
  completadas: number;
  conError: number;
  analizadas: number;
  progresoPercent: number;
  ok: number;
  alerta: number;
  error: number;
  conAlertas: number;
  scorePromedio: number;
}

export interface BatchAnalysisResult {
  batchId: string;
  createdAt: string;
  items: Array<{
    id: string;
    input: AnalysisFileRef;
    output: AnalyzeResponse;
  }>;
  summary: BatchSummary;
}

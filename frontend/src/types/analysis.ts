export interface Metadata {
  filename: string;
  format: string;
  width: number;
  height: number;
  aspectRatio: string;
  fileSizeKb: number;
  colorMode: string;
  iccProfile: string | null;
}

export interface TechnicalValidation {
  formatAllowed: boolean;
  dimensionsValid: boolean;
  fileSizeValid: boolean;
}

export interface ColorItem {
  hex: string;
  percentage: number;
}

export interface ColorAnalysis {
  dominantColors: ColorItem[];
}

export interface AnalyzeResponse {
  meta: Metadata;
  technicalValidation: TechnicalValidation;
  colorAnalysis: ColorAnalysis;
}

export interface ValidationItem {
  key: keyof TechnicalValidation;
  label: string;
  description: string;
  ok: boolean;
}

export type AppStatus = "idle" | "uploading" | "analyzing" | "success" | "error";

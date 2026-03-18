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

export interface OCRWord {
  text: string;
  box: [number, number, number, number];
  confidence: number;
}

export interface OCRConfidence {
  avg: number;
  min: number;
}

export interface OCRResponse {
  rawText: string;
  correctedText: string;
  words: OCRWord[];
  confidence: OCRConfidence;
  score: number | null;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type PieceType = "1:1" | "ST";

export interface LogoDetectionResult {
  detected: boolean;
  bbox?: BoundingBox;
  confidence?: number;
}

export type LogoDetectionStatus = "ok" | "warning";
export type LogoCheckStatus = "ok" | "error" | "not_applicable";

export interface LogoValidationDetails {
  logoDetection: {
    status: LogoDetectionStatus;
    message: string;
    affectsScore: boolean;
  };
  logoPosition: {
    status: LogoCheckStatus;
  };
  logoSize: {
    status: LogoCheckStatus;
  };
}

export interface LayoutValidation {
  pieceType: PieceType | null;
  safeAreaBoundingBox: BoundingBox | null;
  logoDetected: boolean;
  logoWarning: boolean;
  logoDetectionResult?: LogoDetectionResult;
  logoValidation?: LogoValidationDetails;
  logoBoundingBox: BoundingBox | null;
  logoPosition: BoundingBox | null;
  logoSizeValid: boolean;
  logoInsideSafeArea: boolean;
  containerInsideSafeArea: boolean;
  overlapPercentage: number;
  logoPositionValid: boolean;
  logoContainerDetected: boolean;
  logoContainerBoundingBox: BoundingBox | null;
  logoContainerPosition: BoundingBox | null;
  logoContainerSizeValid: boolean;
  textInsideSafeArea: boolean;
  layoutScore: number;
}

export interface AnalyzeResponse {
  meta: Metadata;
  technicalValidation: TechnicalValidation;
  colorAnalysis: ColorAnalysis;
  ocr: OCRResponse | null;
  layoutValidation: LayoutValidation | null;
}

export interface ValidationItem {
  key: keyof TechnicalValidation;
  label: string;
  description: string;
  ok: boolean;
}

export type AppStatus = "idle" | "uploading" | "analyzing" | "success" | "error";

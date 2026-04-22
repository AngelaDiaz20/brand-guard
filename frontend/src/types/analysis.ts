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
  lines?: OCRLine[];
  microBlocks?: OCRMicroBlock[];
  blocks?: OCRBlock[];
  // Region-aware OCR (opcional / debug)
  regions?: OCRRegion[];
  regionalOcr?: RegionalOCRItem[];
  incidentalRegionalOcr?: RegionalOCRItem[];
  regionalLayouts?: RegionalLayout[];
  yoloDetections?: OCRRegion[];
  globalLines?: OCRLine[];
  globalMicroBlocks?: OCRMicroBlock[];
  globalBlocks?: OCRBlock[];
}

export interface OCRLine {
  id?: string;
  text: string;
  bbox: [number, number, number, number];
  confidence: number;
  wordIndexes: number[];
}

export interface OCRBlock {
  id: string;
  type?: string;
  text: string;
  bbox: [number, number, number, number];
  confidence: number;
  wordIndexes: number[];
  lineIndexes: number[];
  lineIds?: string[];
}

export interface OCRMicroBlock extends OCRBlock {
  zone?: string;
}

export interface OCRRegion {
  id: string;
  className?: string;
  kind?: string;
  bbox: [number, number, number, number];
  confidence?: number;
  source?: string;
  excludeFromOcr?: boolean;
}

export interface RegionalOCRItem {
  regionId: string;
  bbox: [number, number, number, number];
  regionClassName?: string | null;
  regionKind?: string | null;
  regionConfidence?: number | null;
  regionSource?: string | null;
  rawText?: string;
  correctedText?: string;
  score?: number | null;
}

export interface RegionalLayout {
  regionId: string;
  bbox: [number, number, number, number];
  lines?: OCRLine[];
  microBlocks?: OCRMicroBlock[];
  blocks?: OCRBlock[];
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
  structuredFields?: StructuredFields | null;
  priceBlockAnalysis?: PriceBlockAnalysis | null;
  excelValidation?: ExcelValidation | null;
}

export interface StructuredFieldValue {
  value: string | null;
  sourceBlockId: string | null;
  confidence: number;
  status: string;
  message?: string | null;
  sourceRegionId?: string | null;
  sourceRegionClassName?: string | null;
  sourceRegionBbox?: [number, number, number, number] | null;
  sourceStrategy?: string | null;
}

export type StructuredFields = Record<string, StructuredFieldValue>;

export interface PriceBlockAnalysis {
  mainBlockDetected: boolean;
  mainBlockBbox: [number, number, number, number] | null;
  mainBlockColor: "red" | "black" | "indeterminate" | string;
  mainBlockColorConfidence: number;
  dominantRgb: [number, number, number] | null;
  classificationStrategy?: string | null;
  messages: string[];
}

export interface ExcelFieldComparison {
  expected: string | null;
  detected: string | null;
  status: string;
  message?: string | null;
}

export interface ExcelValidation {
  enabled: boolean;
  executed: boolean;
  appliesToFormat?: boolean | null;
  matchedRowIndex?: number | null;
  matchStrategy?: string | null;
  overallStatus: string;
  fields: Record<string, ExcelFieldComparison>;
  messages: string[];
}

export interface ValidationItem {
  key: keyof TechnicalValidation;
  label: string;
  description: string;
  ok: boolean;
}

export type AppStatus = "idle" | "uploading" | "analyzing" | "success" | "error";

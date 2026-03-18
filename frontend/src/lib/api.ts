import type { AnalyzeResponse, OCRWord, LayoutValidation, PieceType, LogoDetectionResult, LogoValidationDetails } from "@/types/analysis";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const ANALYZE_ENDPOINT = `${API_BASE_URL}/analyze`;

export class ApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RawColor = {
  hex?: unknown;
  percentage?: unknown;
};

type RawOcrWord = {
  text?: unknown;
  box?: unknown;
  confidence?: unknown;
};

type RawAnalyzeResponse = {
  meta?: AnalyzeResponse["meta"];
  technicalValidation?: AnalyzeResponse["technicalValidation"];
  colorAnalysis?: { dominantColors?: RawColor[] };
  visualAnalysis?: { dominantColors?: RawColor[] };
  layoutValidation?: unknown;
  ocr?: {
    rawText?: unknown;
    correctedText?: unknown;
    words?: RawOcrWord[];
    confidence?: { avg?: unknown; min?: unknown };
    score?: unknown;
  } | null;
};

type RawBoundingBox = {
  x?: unknown;
  y?: unknown;
  width?: unknown;
  height?: unknown;
};

function isBoundingBox(value: unknown): value is { x: number; y: number; width: number; height: number } {
  const box = value as RawBoundingBox;
  return (
    !!box &&
    typeof box === "object" &&
    typeof box.x === "number" &&
    Number.isFinite(box.x) &&
    typeof box.y === "number" &&
    Number.isFinite(box.y) &&
    typeof box.width === "number" &&
    Number.isFinite(box.width) &&
    typeof box.height === "number" &&
    Number.isFinite(box.height)
  );
}

function normalizeAnalyzeResponse(payload: unknown): AnalyzeResponse {
  const response = (payload ?? {}) as RawAnalyzeResponse;
  const fromColorAnalysis = response.colorAnalysis?.dominantColors;
  const fromVisualAnalysis = response.visualAnalysis?.dominantColors;
  const colors = (fromColorAnalysis ?? fromVisualAnalysis ?? [])
    .filter(
      (item): item is { hex: string; percentage: number } =>
        typeof item?.hex === "string" &&
        typeof item?.percentage === "number" &&
        Number.isFinite(item.percentage)
    )
    .map((item) => ({
      hex: item.hex,
      percentage: item.percentage
    }));

  const normalizedOcrWords: OCRWord[] = (response.ocr?.words ?? [])
    .filter(
      (word): word is { text: string; box: [number, number, number, number]; confidence: number } =>
        typeof word?.text === "string" &&
        Array.isArray(word.box) &&
        word.box.length === 4 &&
        word.box.every((point) => typeof point === "number" && Number.isFinite(point)) &&
        typeof word.confidence === "number" &&
        Number.isFinite(word.confidence)
    )
    .map((word) => ({
      text: word.text,
      box: [word.box[0], word.box[1], word.box[2], word.box[3]],
      confidence: word.confidence
    }));

    const rawText =
    response.ocr && typeof response.ocr.rawText === "string" ? response.ocr.rawText : "";

    const correctedText =
      response.ocr && typeof response.ocr.correctedText === "string"
        ? response.ocr.correctedText
        : "";

    const avg =
      response.ocr && typeof response.ocr.confidence?.avg === "number"
        ? response.ocr.confidence.avg
        : 0;

    const min =
      response.ocr && typeof response.ocr.confidence?.min === "number"
        ? response.ocr.confidence.min
        : 0;

    const score =
      response.ocr && (typeof response.ocr.score === "number" || response.ocr.score === null)
        ? (response.ocr.score as number | null)
        : null;

    const normalizedOcr =
      response.ocr && (rawText.trim() || correctedText.trim())
        ? {
            rawText,
            correctedText,
            words: normalizedOcrWords,
            confidence: { avg, min },
            score
          }
        : null;

  const rawLayout = response.layoutValidation as
    | {
        pieceType?: unknown;
        safeAreaBoundingBox?: unknown;
        logoDetected?: unknown;
        logoWarning?: unknown;
        logoDetectionResult?: unknown;
        logoValidation?: unknown;
        logoBoundingBox?: unknown;
        logoPosition?: unknown;
        logoSizeValid?: unknown;
        logoInsideSafeArea?: unknown;
        containerInsideSafeArea?: unknown;
        overlapPercentage?: unknown;
        logoPositionValid?: unknown;
        logoContainerDetected?: unknown;
        logoContainerBoundingBox?: unknown;
        logoContainerPosition?: unknown;
        logoContainerSizeValid?: unknown;
        textInsideSafeArea?: unknown;
        layoutScore?: unknown;
      }
    | undefined;

  const normalizedLayout: LayoutValidation | null =
    rawLayout && typeof rawLayout === "object"
      ? {
          pieceType:
            rawLayout.pieceType === "1:1" || rawLayout.pieceType === "ST"
              ? (rawLayout.pieceType as PieceType)
              : null,
          safeAreaBoundingBox: isBoundingBox(rawLayout.safeAreaBoundingBox) ? rawLayout.safeAreaBoundingBox : null,
          logoDetected: rawLayout.logoDetected === true,
          logoWarning: rawLayout.logoWarning === true,
          logoDetectionResult:
            rawLayout.logoDetectionResult && typeof rawLayout.logoDetectionResult === "object"
              ? (() => {
                  const result = rawLayout.logoDetectionResult as {
                    detected?: unknown;
                    bbox?: unknown;
                    confidence?: unknown;
                  };
                  const detected = result.detected === true;
                  const bbox = isBoundingBox(result.bbox) ? result.bbox : undefined;
                  const confidence =
                    typeof result.confidence === "number" && Number.isFinite(result.confidence)
                      ? result.confidence
                      : undefined;
                  const normalized: LogoDetectionResult = { detected };
                  if (bbox) normalized.bbox = bbox;
                  if (confidence !== undefined) normalized.confidence = confidence;
                  return normalized;
                })()
              : undefined,
          logoValidation:
            rawLayout.logoValidation && typeof rawLayout.logoValidation === "object"
              ? (() => {
                  const lv = rawLayout.logoValidation as {
                    logoDetection?: unknown;
                    logoPosition?: unknown;
                    logoSize?: unknown;
                  };
                  const det = lv.logoDetection as { status?: unknown; message?: unknown; affectsScore?: unknown } | undefined;
                  const pos = lv.logoPosition as { status?: unknown } | undefined;
                  const size = lv.logoSize as { status?: unknown } | undefined;

                  const detectionStatus = det?.status === "ok" || det?.status === "warning" ? det.status : "warning";
                  const detectionMessage = typeof det?.message === "string" ? det.message : "Logo no detectado";
                  const affectsScore = det?.affectsScore === true;

                  const posStatus =
                    pos?.status === "ok" || pos?.status === "error" || pos?.status === "not_applicable"
                      ? pos.status
                      : "not_applicable";
                  const sizeStatus =
                    size?.status === "ok" || size?.status === "error" || size?.status === "not_applicable"
                      ? size.status
                      : "not_applicable";

                  const normalized: LogoValidationDetails = {
                    logoDetection: { status: detectionStatus, message: detectionMessage, affectsScore },
                    logoPosition: { status: posStatus },
                    logoSize: { status: sizeStatus }
                  };
                  return normalized;
                })()
              : undefined,
          logoBoundingBox: isBoundingBox(rawLayout.logoBoundingBox)
            ? rawLayout.logoBoundingBox
            : isBoundingBox(rawLayout.logoPosition)
              ? rawLayout.logoPosition
              : null,
          logoPosition: isBoundingBox(rawLayout.logoPosition)
            ? rawLayout.logoPosition
            : isBoundingBox(rawLayout.logoBoundingBox)
              ? rawLayout.logoBoundingBox
              : null,
          logoSizeValid: rawLayout.logoSizeValid === true,
          logoInsideSafeArea: rawLayout.logoInsideSafeArea === true,
          containerInsideSafeArea: rawLayout.containerInsideSafeArea === true,
          overlapPercentage:
            typeof rawLayout.overlapPercentage === "number" && Number.isFinite(rawLayout.overlapPercentage)
              ? rawLayout.overlapPercentage
              : 0,
          logoPositionValid: rawLayout.logoPositionValid === true,
          logoContainerDetected: rawLayout.logoContainerDetected === true,
          logoContainerBoundingBox: isBoundingBox(rawLayout.logoContainerBoundingBox)
            ? rawLayout.logoContainerBoundingBox
            : isBoundingBox(rawLayout.logoContainerPosition)
              ? rawLayout.logoContainerPosition
              : null,
          logoContainerPosition: isBoundingBox(rawLayout.logoContainerPosition)
            ? rawLayout.logoContainerPosition
            : isBoundingBox(rawLayout.logoContainerBoundingBox)
              ? rawLayout.logoContainerBoundingBox
              : null,
          logoContainerSizeValid: rawLayout.logoContainerSizeValid === true,
          textInsideSafeArea: rawLayout.textInsideSafeArea === false ? false : true,
          layoutScore:
            typeof rawLayout.layoutScore === "number" && Number.isFinite(rawLayout.layoutScore)
              ? rawLayout.layoutScore
              : 0
        }
      : null;

  return {
    meta: response.meta as AnalyzeResponse["meta"],
    technicalValidation: response.technicalValidation as AnalyzeResponse["technicalValidation"],
    colorAnalysis: {
      dominantColors: colors
    },
    ocr: normalizedOcr,
    layoutValidation: normalizedLayout
  };
}

export function analyzeImage(
  file: File,
  onProgress?: (progressPercent: number) => void
): Promise<AnalyzeResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();

    formData.append("file", file);

    xhr.open("POST", ANALYZE_ENDPOINT);
    xhr.responseType = "json";

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) {
        return;
      }

      const percent = Math.round((event.loaded / event.total) * 100);
      onProgress(percent);
    };

    xhr.onerror = () => {
      reject(new ApiError("No se pudo conectar con el backend FastAPI."));
    };

    xhr.onload = () => {
      let responseBody: unknown = xhr.response;

      if (!responseBody && xhr.responseText) {
        try {
          responseBody = JSON.parse(xhr.responseText);
        } catch {
          responseBody = {};
        }
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(normalizeAnalyzeResponse(responseBody));
        return;
      }

      const detail =
        typeof (responseBody as { detail?: unknown })?.detail === "string"
          ? ((responseBody as { detail: string }).detail as string)
          : "Error al analizar la imagen.";
      reject(new ApiError(detail, xhr.status));
    };

    xhr.send(formData);
  });
}

export { ANALYZE_ENDPOINT };

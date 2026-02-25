import type { AnalyzeResponse, OCRWord } from "@/types/analysis";

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
  ocr?: {
    fullText?: unknown;
    words?: RawOcrWord[];
  } | null;
};

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

  const normalizedOcr =
    response.ocr && typeof response.ocr.fullText === "string"
      ? {
          fullText: response.ocr.fullText,
          words: normalizedOcrWords
        }
      : null;

  return {
    meta: response.meta as AnalyzeResponse["meta"],
    technicalValidation: response.technicalValidation as AnalyzeResponse["technicalValidation"],
    colorAnalysis: {
      dominantColors: colors
    },
    ocr: normalizedOcr
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

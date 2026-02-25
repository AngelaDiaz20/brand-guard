import type { AnalyzeResponse } from "@/types/analysis";

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
        resolve(responseBody as AnalyzeResponse);
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

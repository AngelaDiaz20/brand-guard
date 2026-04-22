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

type RawOcrLine = {
  id?: unknown;
  text?: unknown;
  bbox?: unknown;
  confidence?: unknown;
  wordIndexes?: unknown;
};

type RawOcrBlock = {
  id?: unknown;
  type?: unknown;
  zone?: unknown;
  text?: unknown;
  bbox?: unknown;
  confidence?: unknown;
  wordIndexes?: unknown;
  lineIndexes?: unknown;
  lineIds?: unknown;
};

type RawOcrRegion = {
  id?: unknown;
  className?: unknown;
  kind?: unknown;
  bbox?: unknown;
  confidence?: unknown;
  source?: unknown;
  excludeFromOcr?: unknown;
};

type RawRegionalOcrItem = {
  regionId?: unknown;
  bbox?: unknown;
  rawText?: unknown;
  correctedText?: unknown;
  score?: unknown;
  regionClassName?: unknown;
  regionKind?: unknown;
  regionConfidence?: unknown;
  regionSource?: unknown;
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
    lines?: RawOcrLine[] | null;
    microBlocks?: RawOcrBlock[] | null;
    blocks?: RawOcrBlock[] | null;
    regions?: RawOcrRegion[] | null;
    yoloDetections?: RawOcrRegion[] | null;
    regionalOcr?: RawRegionalOcrItem[] | null;
    incidentalRegionalOcr?: RawRegionalOcrItem[] | null;
    globalLines?: RawOcrLine[] | null;
    globalMicroBlocks?: RawOcrBlock[] | null;
    globalBlocks?: RawOcrBlock[] | null;
  } | null;
  structuredFields?: unknown;
  priceBlockAnalysis?: unknown;
  excelValidation?: unknown;
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

  const normalizeLines = (raw: unknown) => {
    if (!normalizedOcr || !Array.isArray(raw)) {
      return undefined;
    }
    return (raw as RawOcrLine[])
      .filter(
        (line): line is {
          id?: unknown;
          text: string;
          bbox: [number, number, number, number];
          confidence: number;
          wordIndexes: number[];
        } =>
          typeof line?.text === "string" &&
          Array.isArray(line.bbox) &&
          line.bbox.length === 4 &&
          line.bbox.every((v) => typeof v === "number" && Number.isFinite(v)) &&
          typeof line.confidence === "number" &&
          Number.isFinite(line.confidence) &&
          Array.isArray(line.wordIndexes) &&
          line.wordIndexes.every((v) => typeof v === "number" && Number.isFinite(v))
      )
      .map((line, index) => ({
        id: typeof line.id === "string" ? line.id : `line_${index + 1}`,
        text: line.text,
        bbox: [line.bbox[0], line.bbox[1], line.bbox[2], line.bbox[3]] as [number, number, number, number],
        confidence: line.confidence,
        wordIndexes: [...line.wordIndexes]
      }));
  };

  const normalizeBlocks = (raw: unknown) => {
    if (!normalizedOcr || !Array.isArray(raw)) {
      return undefined;
    }
    return (raw as RawOcrBlock[])
      .filter(
        (block): block is {
          id: string;
          type?: unknown;
          zone?: unknown;
          text: string;
          bbox: [number, number, number, number];
          confidence: number;
          wordIndexes: number[];
          lineIndexes: number[];
          lineIds?: unknown;
        } =>
          typeof block?.id === "string" &&
          typeof block?.text === "string" &&
          Array.isArray(block.bbox) &&
          block.bbox.length === 4 &&
          block.bbox.every((v) => typeof v === "number" && Number.isFinite(v)) &&
          typeof block.confidence === "number" &&
          Number.isFinite(block.confidence) &&
          Array.isArray(block.wordIndexes) &&
          block.wordIndexes.every((v) => typeof v === "number" && Number.isFinite(v)) &&
          Array.isArray(block.lineIndexes) &&
          block.lineIndexes.every((v) => typeof v === "number" && Number.isFinite(v))
      )
      .map((block) => ({
        id: block.id,
        type: typeof block.type === "string" ? block.type : undefined,
        zone: typeof block.zone === "string" ? block.zone : undefined,
        text: block.text,
        bbox: [block.bbox[0], block.bbox[1], block.bbox[2], block.bbox[3]] as [number, number, number, number],
        confidence: block.confidence,
        wordIndexes: [...block.wordIndexes],
        lineIndexes: [...block.lineIndexes],
        lineIds: Array.isArray(block.lineIds) ? block.lineIds.filter((v): v is string => typeof v === "string") : undefined
      }));
  };

  const normalizedOcrLines = normalizeLines(response.ocr?.lines);
  const normalizedOcrBlocks = normalizeBlocks(response.ocr?.blocks);
  const normalizedOcrMicroBlocks = normalizeBlocks(response.ocr?.microBlocks);
  const normalizedOcrRegions = normalizeRegions(response.ocr?.regions);
  const normalizedOcrYoloDetections = normalizeRegions(response.ocr?.yoloDetections);
  const normalizedOcrRegionalOcr = normalizeRegionalOcr(response.ocr?.regionalOcr);
  const normalizedOcrIncidentalRegionalOcr = normalizeRegionalOcr(response.ocr?.incidentalRegionalOcr);
  const normalizedOcrGlobalLines = normalizeLines(response.ocr?.globalLines);
  const normalizedOcrGlobalBlocks = normalizeBlocks(response.ocr?.globalBlocks);
  const normalizedOcrGlobalMicroBlocks = normalizeBlocks(response.ocr?.globalMicroBlocks);

  function normalizeRegions(raw: unknown) {
    if (!normalizedOcr || !Array.isArray(raw)) {
      return undefined;
    }
    return (raw as RawOcrRegion[])
      .filter(
        (r): r is { id: string; bbox: [number, number, number, number] } =>
          typeof r?.id === "string" &&
          Array.isArray(r.bbox) &&
          r.bbox.length === 4 &&
          r.bbox.every((v) => typeof v === "number" && Number.isFinite(v))
      )
      .map((r) => ({
        id: r.id as string,
        className: typeof r.className === "string" ? r.className : undefined,
        kind: typeof r.kind === "string" ? r.kind : undefined,
        bbox: [r.bbox![0], r.bbox![1], r.bbox![2], r.bbox![3]] as [number, number, number, number],
        confidence: typeof r.confidence === "number" && Number.isFinite(r.confidence) ? r.confidence : undefined,
        source: typeof r.source === "string" ? r.source : undefined,
        excludeFromOcr: r.excludeFromOcr === true ? true : undefined
      }));
  }

  function normalizeRegionalOcr(raw: unknown) {
    if (!normalizedOcr || !Array.isArray(raw)) {
      return undefined;
    }
    return (raw as RawRegionalOcrItem[])
      .filter(
        (r): r is { regionId: string; bbox: [number, number, number, number] } =>
          typeof r?.regionId === "string" &&
          Array.isArray(r.bbox) &&
          r.bbox.length === 4 &&
          r.bbox.every((v) => typeof v === "number" && Number.isFinite(v))
      )
      .map((r) => ({
        regionId: r.regionId as string,
        bbox: [r.bbox![0], r.bbox![1], r.bbox![2], r.bbox![3]] as [number, number, number, number],
        regionClassName: typeof r.regionClassName === "string" ? r.regionClassName : null,
        regionKind: typeof r.regionKind === "string" ? r.regionKind : null,
        regionConfidence:
          typeof r.regionConfidence === "number" && Number.isFinite(r.regionConfidence) ? r.regionConfidence : null,
        regionSource: typeof r.regionSource === "string" ? r.regionSource : null,
        rawText: typeof r.rawText === "string" ? r.rawText : undefined,
        correctedText: typeof r.correctedText === "string" ? r.correctedText : undefined,
        score: typeof r.score === "number" && Number.isFinite(r.score) ? r.score : null
      }));
  }

  const normalizedStructuredFields =
    response.structuredFields && typeof response.structuredFields === "object"
      ? Object.fromEntries(
          Object.entries(response.structuredFields as Record<string, unknown>)
            .filter(([key]) => typeof key === "string" && key.length > 0)
            .map(([key, value]) => {
              const field = (value ?? {}) as {
                value?: unknown;
                sourceBlockId?: unknown;
                confidence?: unknown;
                status?: unknown;
                message?: unknown;
                sourceRegionId?: unknown;
                sourceRegionClassName?: unknown;
                sourceRegionBbox?: unknown;
                sourceStrategy?: unknown;
              };
              const normalized = {
                value: typeof field.value === "string" ? field.value : field.value === null ? null : null,
                sourceBlockId: typeof field.sourceBlockId === "string" ? field.sourceBlockId : null,
                confidence: typeof field.confidence === "number" && Number.isFinite(field.confidence) ? field.confidence : 0,
                status: typeof field.status === "string" ? field.status : "not_detected",
                message: typeof field.message === "string" ? field.message : null,
                sourceRegionId: typeof field.sourceRegionId === "string" ? field.sourceRegionId : null,
                sourceRegionClassName: typeof field.sourceRegionClassName === "string" ? field.sourceRegionClassName : null,
                sourceRegionBbox:
                  Array.isArray(field.sourceRegionBbox) &&
                  field.sourceRegionBbox.length === 4 &&
                  field.sourceRegionBbox.every((v) => typeof v === "number" && Number.isFinite(v))
                    ? ([field.sourceRegionBbox[0], field.sourceRegionBbox[1], field.sourceRegionBbox[2], field.sourceRegionBbox[3]] as [
                        number,
                        number,
                        number,
                        number
                      ])
                    : null,
                sourceStrategy: typeof field.sourceStrategy === "string" ? field.sourceStrategy : null
              };
              return [key, normalized];
            })
        )
      : null;

  const normalizedPriceBlockAnalysis =
    response.priceBlockAnalysis && typeof response.priceBlockAnalysis === "object"
      ? (() => {
          const p = response.priceBlockAnalysis as {
            mainBlockDetected?: unknown;
            mainBlockBbox?: unknown;
            mainBlockColor?: unknown;
            mainBlockColorConfidence?: unknown;
            dominantRgb?: unknown;
            classificationStrategy?: unknown;
            messages?: unknown;
          };
          const bbox =
            Array.isArray(p.mainBlockBbox) &&
            p.mainBlockBbox.length === 4 &&
            p.mainBlockBbox.every((v) => typeof v === "number" && Number.isFinite(v))
              ? ([p.mainBlockBbox[0], p.mainBlockBbox[1], p.mainBlockBbox[2], p.mainBlockBbox[3]] as [number, number, number, number])
              : null;
          const rgb =
            Array.isArray(p.dominantRgb) &&
            p.dominantRgb.length === 3 &&
            p.dominantRgb.every((v) => typeof v === "number" && Number.isFinite(v))
              ? ([p.dominantRgb[0], p.dominantRgb[1], p.dominantRgb[2]] as [number, number, number])
              : null;
          const messages = Array.isArray(p.messages) ? p.messages.filter((m): m is string => typeof m === "string") : [];
          return {
            mainBlockDetected: p.mainBlockDetected === true,
            mainBlockBbox: bbox,
            mainBlockColor: typeof p.mainBlockColor === "string" ? p.mainBlockColor : "indeterminate",
            mainBlockColorConfidence:
              typeof p.mainBlockColorConfidence === "number" && Number.isFinite(p.mainBlockColorConfidence)
                ? p.mainBlockColorConfidence
                : 0,
            dominantRgb: rgb,
            classificationStrategy: typeof p.classificationStrategy === "string" ? p.classificationStrategy : null,
            messages
          };
        })()
      : null;

  const normalizedExcelValidation =
    response.excelValidation && typeof response.excelValidation === "object"
      ? (() => {
          const ev = response.excelValidation as {
            enabled?: unknown;
            executed?: unknown;
            appliesToFormat?: unknown;
            matchedRowIndex?: unknown;
            matchStrategy?: unknown;
            overallStatus?: unknown;
            fields?: unknown;
            messages?: unknown;
          };

          const fields =
            ev.fields && typeof ev.fields === "object"
              ? Object.fromEntries(
                  Object.entries(ev.fields as Record<string, unknown>).map(([key, value]) => {
                    const f = (value ?? {}) as { expected?: unknown; detected?: unknown; status?: unknown; message?: unknown };
                    return [
                      key,
                      {
                        expected: typeof f.expected === "string" ? f.expected : f.expected === null ? null : null,
                        detected: typeof f.detected === "string" ? f.detected : f.detected === null ? null : null,
                        status: typeof f.status === "string" ? f.status : "unknown",
                        message: typeof f.message === "string" ? f.message : null
                      }
                    ];
                  })
                )
              : {};

          const messages = Array.isArray(ev.messages) ? ev.messages.filter((m): m is string => typeof m === "string") : [];

          return {
            enabled: ev.enabled === true,
            executed: ev.executed === true,
            appliesToFormat: typeof ev.appliesToFormat === "boolean" ? ev.appliesToFormat : null,
            matchedRowIndex: typeof ev.matchedRowIndex === "number" && Number.isFinite(ev.matchedRowIndex) ? ev.matchedRowIndex : null,
            matchStrategy: typeof ev.matchStrategy === "string" ? ev.matchStrategy : null,
            overallStatus: typeof ev.overallStatus === "string" ? ev.overallStatus : "unknown",
            fields,
            messages
          };
        })()
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
    ocr: normalizedOcr
      ? {
          ...normalizedOcr,
          lines: normalizedOcrLines,
          microBlocks: normalizedOcrMicroBlocks,
          blocks: normalizedOcrBlocks,
          regions: normalizedOcrRegions,
          yoloDetections: normalizedOcrYoloDetections,
          regionalOcr: normalizedOcrRegionalOcr,
          incidentalRegionalOcr: normalizedOcrIncidentalRegionalOcr,
          globalLines: normalizedOcrGlobalLines,
          globalMicroBlocks: normalizedOcrGlobalMicroBlocks,
          globalBlocks: normalizedOcrGlobalBlocks
        }
      : null,
    layoutValidation: normalizedLayout,
    structuredFields: normalizedStructuredFields,
    priceBlockAnalysis: normalizedPriceBlockAnalysis,
    excelValidation: normalizedExcelValidation
  };
}

type AnalyzeImageOptions = {
  excelFile?: File | null;
  pieceFormat?: string | null;
  debug?: boolean;
};

export function analyzeImage(file: File, onProgress?: (progressPercent: number) => void): Promise<AnalyzeResponse>;
export function analyzeImage(
  file: File,
  options?: AnalyzeImageOptions,
  onProgress?: (progressPercent: number) => void
): Promise<AnalyzeResponse>;
export function analyzeImage(
  file: File,
  optionsOrProgress?: AnalyzeImageOptions | ((progressPercent: number) => void),
  onProgress?: (progressPercent: number) => void
): Promise<AnalyzeResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();

    formData.append("file", file);

    const options: AnalyzeImageOptions =
      typeof optionsOrProgress === "function" ? {} : (optionsOrProgress ?? {});
    const progressCb = typeof optionsOrProgress === "function" ? optionsOrProgress : onProgress;

    if (options.excelFile) {
      formData.append("excel_file", options.excelFile);
    }
    if (options.pieceFormat) {
      formData.append("piece_format", options.pieceFormat);
    }
    if (options.debug) {
      formData.append("debug", "true");
    }

    xhr.open("POST", ANALYZE_ENDPOINT);
    xhr.responseType = "json";

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !progressCb) {
        return;
      }

      const percent = Math.round((event.loaded / event.total) * 100);
      progressCb(percent);
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

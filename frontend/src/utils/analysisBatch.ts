import type { AnalyzeResponse } from "@/types/analysis";
import type { AnalysisCardData, AnalysisCardIndicator, AnalysisItem, AnalysisStatus, BatchSummary, IndicatorState } from "@/types/analysisBatch";
import { calculateScore, getValidationItems } from "@/utils/analysis";

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function scoreFromResult(result: AnalyzeResponse): number {
  const scores: number[] = [];

  scores.push(calculateScore(result.technicalValidation));

  if (result.layoutValidation) {
    scores.push(clampScore(result.layoutValidation.layoutScore));
  }

  if (typeof result.ocr?.score === "number") {
    scores.push(clampScore(result.ocr.score));
  }

  if (scores.length === 0) return 0;
  return clampScore(scores.reduce((acc, current) => acc + current, 0) / scores.length);
}

function deriveStatusFromResult(result: AnalyzeResponse): AnalysisStatus {
  const technicalItems = getValidationItems(result.technicalValidation);
  const passed = technicalItems.filter((item) => item.ok).length;

  if (!result.technicalValidation.formatAllowed) {
    return "error";
  }

  if (passed !== technicalItems.length) {
    return "alerta";
  }

  const layout = result.layoutValidation;
  if (!layout) {
    return "ok";
  }

  const hasHardLayoutError =
    (layout.logoValidation?.logoPosition.status ?? "not_applicable") === "error" ||
    (layout.logoValidation?.logoSize.status ?? "not_applicable") === "error" ||
    layout.textInsideSafeArea === false;

  if (hasHardLayoutError) {
    return "alerta";
  }

  if (layout.logoWarning) {
    return "alerta";
  }

  return "ok";
}

function indicator(label: string, key: string, state: IndicatorState): AnalysisCardIndicator {
  return { label, key, state };
}

export type FindingSeverity = "ok" | "alerta" | "error";

export interface BatchFinding {
  key: string;
  label: string;
  count: number;
  severity: FindingSeverity;
}

function addFinding(
  target: Map<string, BatchFinding>,
  key: string,
  label: string,
  severity: FindingSeverity
) {
  const existing = target.get(key);
  if (existing) {
    existing.count += 1;
    return;
  }
  target.set(key, { key, label, count: 1, severity });
}

export function buildBatchFindings(items: AnalysisItem[]): BatchFinding[] {
  const findings = new Map<string, BatchFinding>();

  items.forEach((item) => {
    if (item.state !== "listo") {
      return;
    }

    const result: AnalyzeResponse = item.output;
    const layout = result.layoutValidation;

    const technical = result.technicalValidation;
    if (!technical.formatAllowed) addFinding(findings, "format_not_allowed", "Formato no permitido", "error");
    if (!technical.dimensionsValid) addFinding(findings, "dimensions_invalid", "Dimensiones no válidas", "alerta");
    if (!technical.fileSizeValid) addFinding(findings, "file_size_invalid", "Peso del archivo excedido", "alerta");

    if (layout) {
      const logoDetected = layout.logoDetectionResult?.detected ?? layout.logoDetected;
      if (!logoDetected) {
        addFinding(findings, "logo_missing", "Logo no detectado", "alerta");
      }

      if (layout.logoWarning) {
        addFinding(findings, "logo_warning", "Observación en detección de logo", "alerta");
      }

      const posStatus = layout.logoValidation?.logoPosition.status ?? "not_applicable";
      if (posStatus === "error") {
        addFinding(findings, "logo_position_error", "Problemas de posición del logo", "error");
      }

      const sizeStatus = layout.logoValidation?.logoSize.status ?? "not_applicable";
      if (sizeStatus === "error") {
        addFinding(findings, "logo_size_error", "Problemas de tamaño del logo", "error");
      }

      if (layout.textInsideSafeArea === false) {
        addFinding(findings, "text_outside_safe_area", "Texto fuera del área segura", "error");
      } else if (layout.textInsideSafeArea === true) {
        addFinding(findings, "text_inside_safe_area", "Texto dentro del área segura", "ok");
      }

      if (layout.logoContainerDetected === false) {
        addFinding(findings, "logo_container_missing", "Contenedor del logo no detectado", "alerta");
      }
    }

    const ocr = result.ocr;
    if (ocr) {
      const raw = ocr.rawText?.trim?.() ? String(ocr.rawText).trim() : "";
      const corrected = ocr.correctedText?.trim?.() ? String(ocr.correctedText).trim() : "";
      if (raw && corrected && raw !== corrected) {
        addFinding(findings, "ocr_corrections", "Observaciones OCR (texto corregido)", "alerta");
      }
      if (typeof ocr.confidence?.avg === "number" && ocr.confidence.avg > 0 && ocr.confidence.avg < 0.7) {
        addFinding(findings, "ocr_low_confidence", "Baja confianza OCR", "alerta");
      }
    }
  });

  return Array.from(findings.values()).sort((a, b) => b.count - a.count);
}

export function buildCardDataFromItem(item: AnalysisItem): AnalysisCardData {
  const base = {
    id: item.id,
    fileName: item.input.fileName,
    previewUrl: item.input.previewUrl,
    fileType: item.input.fileType
  };

  if (item.state !== "listo") {
    return {
      ...base,
      format: "—",
      pieceType: null,
      scoreGeneral: 0,
      statusGeneral: item.state === "error" ? "error" : "alerta",
      indicators: [
        indicator("Área segura", "safe_area", "no_aplica"),
        indicator("Logo", "logo", "no_aplica"),
        indicator("Texto en área segura", "text_safe_area", "no_aplica"),
        indicator("Contenedor del logo", "logo_container", "no_aplica"),
        indicator("Validación general", "overall", "no_aplica")
      ]
    };
  }

  const result = item.output;
  const layout = result.layoutValidation;

  const format = result.meta?.format ? String(result.meta.format) : "—";
  const pieceType = layout?.pieceType ?? null;
  const scoreGeneral = scoreFromResult(result);
  const statusGeneral = deriveStatusFromResult(result);

  const safeAreaState: IndicatorState = layout ? "ok" : "no_aplica";

  const logoDetectionStatus = layout?.logoValidation?.logoDetection.status ?? null;
  const logoDetected = layout ? (layout.logoDetectionResult?.detected ?? layout.logoDetected) : null;
  const logoState: IndicatorState =
    layout === null
      ? "no_aplica"
      : logoDetectionStatus === "ok" && logoDetected
        ? "ok"
        : logoDetectionStatus === "warning"
          ? "alerta"
          : logoDetected
            ? "ok"
            : "error";

  const textSafeAreaState: IndicatorState = layout
    ? layout.textInsideSafeArea
      ? "ok"
      : "error"
    : "no_aplica";

  const logoContainerState: IndicatorState = layout
    ? layout.logoContainerDetected
      ? layout.logoContainerSizeValid && layout.containerInsideSafeArea
        ? "ok"
        : "alerta"
      : "alerta"
    : "no_aplica";

  const indicators: AnalysisCardIndicator[] = [
    indicator("Área segura", "safe_area", safeAreaState),
    indicator("Logo", "logo", logoState),
    indicator("Texto en área segura", "text_safe_area", textSafeAreaState),
    indicator("Contenedor del logo", "logo_container", logoContainerState),
    indicator(
      "Validación general",
      "overall",
      statusGeneral === "ok" ? "ok" : statusGeneral === "error" ? "error" : "alerta"
    )
  ];

  return {
    ...base,
    format,
    pieceType,
    scoreGeneral,
    statusGeneral,
    indicators
  };
}

export function buildBatchSummary(items: AnalysisItem[], cards: AnalysisCardData[]): BatchSummary {
  const total = items.length;
  const pendientes = items.filter((item) => item.state === "pendiente").length;
  const enProceso = items.filter((item) => item.state === "subiendo" || item.state === "analizando").length;
  const completadas = items.filter((item) => item.state === "listo").length;
  const conError = items.filter((item) => item.state === "error").length;
  const analizadas = completadas + conError;

  const progressUnit = (item: AnalysisItem): number => {
    if (item.state === "listo" || item.state === "error") {
      return 1;
    }
    if (item.state === "analizando") {
      return 0.5;
    }
    if (item.state === "subiendo") {
      const p = typeof item.progressPercent === "number" ? clampScore(item.progressPercent) : 0;
      return 0.5 * (p / 100);
    }
    return 0;
  };
  const progresoPercent =
    total === 0 ? 0 : clampScore((items.reduce((acc, item) => acc + progressUnit(item), 0) / total) * 100);

  const completedCards = cards.filter((_, index) => items[index]?.state === "listo");
  const ok = completedCards.filter((card) => card.statusGeneral === "ok").length;
  const alerta = completedCards.filter((card) => card.statusGeneral === "alerta").length;
  const error = completedCards.filter((card) => card.statusGeneral === "error").length;
  const conAlertas = alerta + error;

  const scorePromedio =
    completadas === 0
      ? 0
      : clampScore(completedCards.reduce((acc, card) => acc + clampScore(card.scoreGeneral), 0) / completadas);

  return {
    total,
    pendientes,
    enProceso,
    completadas,
    conError,
    analizadas,
    progresoPercent,
    ok,
    alerta,
    error,
    conAlertas,
    scorePromedio
  };
}

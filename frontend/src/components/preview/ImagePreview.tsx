"use client";

import { useEffect, useRef } from "react";

import { layoutRules as staticLayoutRules } from "@/config/layoutRules";
import { computeSafeAreaBoundingBox, detectPieceType } from "@/config/safeAreaRules";
import type { AnalyzeResponse } from "@/types/analysis";
import type { UploadFileType } from "@/types/upload";

interface ImagePreviewProps {
  fileUrl: string;
  fileType: UploadFileType;
  result?: AnalyzeResponse | null;
}

type DrawBox = { x: number; y: number; width: number; height: number };

function drawBox(
  ctx: CanvasRenderingContext2D,
  box: DrawBox,
  color: string,
  label?: string,
  options?: { dashed?: boolean }
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  if (options?.dashed) {
    ctx.setLineDash([6, 4]);
  }
  ctx.strokeRect(box.x, box.y, box.width, box.height);
  if (label) {
    ctx.fillStyle = color;
    ctx.font = "12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.fillText(label, box.x + 6, Math.max(14, box.y - 6));
  }
  ctx.restore();
}

export function ImagePreview({ fileUrl, fileType, result }: ImagePreviewProps) {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (fileType === "pdf") {
      return;
    }

    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) {
      return;
    }

    const draw = () => {
      const layout = result?.layoutValidation ?? null;
      const meta = result?.meta ?? null;
      if (!layout || !meta) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        return;
      }

      const displayW = img.clientWidth;
      const displayH = img.clientHeight;
      if (!displayW || !displayH) {
        return;
      }

      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(displayW * dpr);
      canvas.height = Math.round(displayH * dpr);
      canvas.style.width = `${displayW}px`;
      canvas.style.height = `${displayH}px`;

      const ctx = canvas.getContext("2d");
      if (!ctx) {
        return;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, displayW, displayH);

      const sx = displayW / meta.width;
      const sy = displayH / meta.height;

      const yoloRegions = result?.ocr?.yoloDetections ?? null;
      if (Array.isArray(yoloRegions) && yoloRegions.length > 0) {
        const max = Math.min(10, yoloRegions.length);
        for (let i = 0; i < max; i++) {
          const r = yoloRegions[i];
          const [x, y, w, h] = r.bbox;
          drawBox(
            ctx,
            { x: x * sx, y: y * sy, width: w * sx, height: h * sy },
            "rgba(234, 179, 8, 0.85)",
            r.className ? `YOLO: ${r.className}` : `YOLO: ${r.id}`,
            { dashed: true }
          );
        }
      }

      const ocrRegions = result?.ocr?.regions ?? null;
      if (Array.isArray(ocrRegions) && ocrRegions.length > 0) {
        const max = Math.min(10, ocrRegions.length);
        for (let i = 0; i < max; i++) {
          const r = ocrRegions[i];
          const [x, y, w, h] = r.bbox;
          drawBox(
            ctx,
            { x: x * sx, y: y * sy, width: w * sx, height: h * sy },
            "rgba(168, 85, 247, 0.85)",
            r.className ? `OCR: ${r.className}` : `OCR: ${r.id}`,
            { dashed: true }
          );
        }
      }

      const safe =
        layout.safeAreaBoundingBox ??
        (() => {
          const fallbackType = layout.pieceType ?? detectPieceType(meta.width, meta.height);
          if (!fallbackType) {
            return null;
          }
          return computeSafeAreaBoundingBox(fallbackType, meta.width, meta.height);
        })();

      if (safe) {
        drawBox(
          ctx,
          {
            x: safe.x * sx,
            y: safe.y * sy,
            width: safe.width * sx,
            height: safe.height * sy
          },
          "rgba(59, 130, 246, 0.9)",
          "Área segura"
        );
      }

      const pieceType = layout.pieceType ?? detectPieceType(meta.width, meta.height);
      const staticKey = pieceType === "ST" ? "9:16" : pieceType === "1:1" ? "1:1" : null;

      if (staticKey) {
        const expected = staticLayoutRules[staticKey].logo.expected;
        const masterWidth = 1080;
        const masterHeight = staticKey === "9:16" ? 1920 : 1080;

        // IMPORTANT: expected.x/expected.y are treated as CENTER coordinates in the master canvas.
        const expectedMasterX = expected.x - expected.width / 2;
        const expectedMasterY = expected.y - expected.height / 2;

        // Master -> image -> display mapping (deterministic; no dependency on detection).
        const masterToImageX = meta.width / masterWidth;
        const masterToImageY = meta.height / masterHeight;
        const expectedImage = {
          x: expectedMasterX * masterToImageX,
          y: expectedMasterY * masterToImageY,
          width: expected.width * masterToImageX,
          height: expected.height * masterToImageY
        };

        drawBox(
          ctx,
          {
            x: expectedImage.x * sx,
            y: expectedImage.y * sy,
            width: expectedImage.width * sx,
            height: expectedImage.height * sy
          },
          "rgba(234, 179, 8, 0.95)",
          "Logo esperado",
          { dashed: true }
        );
      }

      const logoDetectionStatus =
        layout.logoValidation?.logoDetection.status ?? (layout.logoDetected ? "ok" : "warning");
      const logoDetectionFlag = layout.logoDetectionResult?.detected ?? layout.logoDetected;
      const detectedLogoBox =
        layout.logoDetectionResult?.bbox ?? layout.logoBoundingBox ?? layout.logoPosition ?? null;

      if (logoDetectionStatus === "ok" && logoDetectionFlag && detectedLogoBox) {
        const ok = layout.logoInsideSafeArea && layout.logoSizeValid && layout.logoPositionValid;
        const box = detectedLogoBox;
        drawBox(
          ctx,
          {
            x: box.x * sx,
            y: box.y * sy,
            width: box.width * sx,
            height: box.height * sy
          },
          ok ? "rgba(16, 185, 129, 0.95)" : "rgba(239, 68, 68, 0.95)",
          "Logo"
        );
      }

      if (layout.logoContainerDetected && layout.logoContainerPosition) {
        const box = layout.logoContainerBoundingBox ?? layout.logoContainerPosition;
        drawBox(
          ctx,
          {
            x: box.x * sx,
            y: box.y * sy,
            width: box.width * sx,
            height: box.height * sy
          },
          layout.logoContainerSizeValid
            ? "rgba(16, 185, 129, 0.8)"
            : "rgba(239, 68, 68, 0.8)",
          "Contenedor"
        );
      }
    };

    const onResize = () => draw();

    window.addEventListener("resize", onResize);
    draw();

    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, [fileType, result]);

  if (fileType === "pdf") {
    return (
      <div className="rounded-xl bg-gray-100 p-6 shadow-inner">
        <div className="rounded-xl bg-white p-2 shadow-md">
          <iframe
            src={fileUrl}
            title="Vista previa del PDF seleccionado"
            className="h-[500px] w-full rounded-lg border border-slate-200"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-gray-100 p-6 shadow-inner">
      <div className="flex justify-center rounded-xl bg-white p-4 shadow-md">
        <div className="relative">
          <img
            ref={imgRef}
            src={fileUrl}
            alt="Vista previa de la imagen seleccionada"
            className="h-auto max-h-[500px] w-auto max-w-full object-contain"
            onLoad={() => {
              const canvas = canvasRef.current;
              const img = imgRef.current;
              if (!canvas || !img) {
                return;
              }
              canvas.style.width = `${img.clientWidth}px`;
              canvas.style.height = `${img.clientHeight}px`;
            }}
          />
          <canvas
            ref={canvasRef}
            className="pointer-events-none absolute left-0 top-0"
            aria-label="Capa de validación de layout"
          />
        </div>
      </div>
    </div>
  );
}

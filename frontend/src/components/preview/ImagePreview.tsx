"use client";

import { useEffect, useRef } from "react";

import { computeSafeAreaBoundingBox, detectPieceType } from "@/config/layoutRules";
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
  label?: string
) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
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

      if (layout.logoDetected && layout.logoPosition) {
        const ok = layout.logoInsideSafeArea && layout.logoSizeValid && layout.logoPositionValid;
        const box = layout.logoBoundingBox ?? layout.logoPosition;
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

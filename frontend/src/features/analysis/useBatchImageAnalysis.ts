"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ApiError, analyzeImage } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/analysis";
import type { AnalysisItem } from "@/types/analysisBatch";
import { getUploadFileType } from "@/types/upload";

function createLocalId(prefix = "pieza") {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${suffix}`;
}

async function allSettledWithConcurrency<TInput, TValue>(
  inputs: TInput[],
  limit: number,
  worker: (input: TInput, index: number) => Promise<TValue>
): Promise<Array<PromiseSettledResult<TValue>>> {
  const results: Array<PromiseSettledResult<TValue>> = new Array(inputs.length);
  let nextIndex = 0;

  const runners = Array.from({ length: Math.max(1, Math.min(limit, inputs.length)) }, async () => {
    while (true) {
      const currentIndex = nextIndex;
      nextIndex += 1;
      if (currentIndex >= inputs.length) {
        return;
      }

      try {
        const value = await worker(inputs[currentIndex]!, currentIndex);
        results[currentIndex] = { status: "fulfilled", value };
      } catch (reason) {
        results[currentIndex] = { status: "rejected", reason };
      }
    }
  });

  await Promise.all(runners);
  return results;
}

export type BatchAnalyzeOrder = "nombre" | "estado" | "score_alto" | "score_bajo";
export type BatchAnalyzeFilter = "todas" | "correctas" | "alertas" | "error";

export function useBatchImageAnalysis({ maxConcurrency = 3 }: { maxConcurrency?: number } = {}) {
  const [items, setItems] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const objectUrlsRef = useRef<Set<string>>(new Set());
  const runIdRef = useRef<string | null>(null);

  useEffect(() => {
    const urls = objectUrlsRef.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

  const isBusy = useMemo(
    () => loading || items.some((item) => item.state === "subiendo" || item.state === "analizando"),
    [loading, items]
  );

  const createPreviewUrl = (file: File) => {
    const url = URL.createObjectURL(file);
    objectUrlsRef.current.add(url);
    return url;
  };

  const revokePreviewUrl = (url: string) => {
    try {
      URL.revokeObjectURL(url);
    } finally {
      objectUrlsRef.current.delete(url);
    }
  };

  const addFiles = (files: File[]) => {
    if (!files.length) {
      return;
    }

    const validItems: AnalysisItem[] = [];
    let invalidCount = 0;

    for (const file of files) {
      const fileType = getUploadFileType(file);
      if (!fileType) {
        invalidCount += 1;
        continue;
      }

      const id = createLocalId("pieza");
      validItems.push({
        id,
        input: {
          id,
          file,
          fileName: file.name,
          fileType,
          previewUrl: createPreviewUrl(file)
        },
        state: "pendiente"
      });
    }

    if (validItems.length === 0) {
      setErrorMessage("No se encontraron archivos válidos para analizar.");
      if (invalidCount > 0) {
        setInfoMessage(null);
      }
      return;
    }

    setErrorMessage(null);
    setInfoMessage(
      invalidCount > 0
        ? `Se ignoraron ${invalidCount} archivo${invalidCount === 1 ? "" : "s"} no válido${invalidCount === 1 ? "" : "s"}.`
        : null
    );

    setItems((previous) => [...previous, ...validItems]);
  };

  const removeItem = (id: string) => {
    setItems((previous) => {
      const item = previous.find((current) => current.id === id);
      if (item) {
        revokePreviewUrl(item.input.previewUrl);
      }
      return previous.filter((current) => current.id !== id);
    });
  };

  const clearBatch = () => {
    items.forEach((item) => revokePreviewUrl(item.input.previewUrl));
    setItems([]);
    setErrorMessage(null);
    setInfoMessage(null);
  };

  const analyzeIds = async (ids: string[]) => {
    const snapshot = items;
    const targets = snapshot.filter((item) => ids.includes(item.id));
    if (targets.length === 0) {
      return;
    }

    const runId = createLocalId("lote");
    runIdRef.current = runId;

    setErrorMessage(null);
    setLoading(true);

    setItems((previous) =>
      previous.map((item) => {
        if (!ids.includes(item.id)) {
          return item;
        }
        return { id: item.id, input: item.input, state: "pendiente" };
      })
    );

    const settled = await allSettledWithConcurrency(
      targets,
      maxConcurrency,
      async (item): Promise<{ id: string; output: AnalyzeResponse }> => {
        if (runIdRef.current !== runId) {
          throw new Error("El análisis fue cancelado.");
        }

        const startedAtMs = Date.now();
        setItems((previous) =>
          previous.map((current) =>
            current.id === item.id
              ? {
                  id: current.id,
                  input: current.input,
                  state: "subiendo",
                  progressPercent: 0,
                  startedAtMs
                }
              : current
          )
        );

        const file = item.input.file;
        if (!file) {
          throw new Error("No se encontró el archivo asociado a esta pieza.");
        }

        const output = await analyzeImage(file, (progressPercent) => {
          if (runIdRef.current !== runId) {
            return;
          }

          setItems((previous) =>
            previous.map((current) => {
              if (current.id !== item.id) {
                return current;
              }
              if (current.state !== "subiendo" && current.state !== "analizando") {
                return current;
              }

              const normalized = Math.max(0, Math.min(100, Math.round(progressPercent)));
              return {
                ...current,
                progressPercent: normalized,
                state: normalized >= 100 ? "analizando" : "subiendo"
              };
            })
          );
        });

        return { id: item.id, output };
      }
    );

    if (runIdRef.current !== runId) {
      setLoading(false);
      return;
    }

    const finishedAtMs = Date.now();

    setItems((previous) => {
      const byId = new Map(previous.map((item) => [item.id, item]));
      settled.forEach((result, index) => {
        const target = targets[index]!;
        const current = byId.get(target.id);
        if (!current) {
          return;
        }

        if (result.status === "fulfilled") {
          byId.set(target.id, {
            id: target.id,
            input: current.input,
            state: "listo",
            output: result.value.output,
            startedAtMs: current.startedAtMs,
            finishedAtMs
          });
          return;
        }

        const reason = result.reason as unknown;
        const message =
          reason instanceof ApiError
            ? reason.message
            : reason instanceof Error
              ? reason.message
              : "No se pudo analizar la imagen.";

        byId.set(target.id, {
          id: target.id,
          input: current.input,
          state: "error",
          error: message,
          startedAtMs: current.startedAtMs,
          finishedAtMs
        });
      });

      return previous.map((item) => byId.get(item.id) ?? item);
    });

    setLoading(false);
  };

  const analyzeBatch = async () => {
    if (isBusy) {
      return;
    }
    const ids = items.filter((item) => item.state === "pendiente" || item.state === "error").map((item) => item.id);
    if (ids.length === 0) {
      return;
    }
    await analyzeIds(ids);
  };

  const retryItem = async (id: string) => {
    if (isBusy) {
      return;
    }
    await analyzeIds([id]);
  };

  return {
    items,
    isBusy,
    loading,
    errorMessage,
    infoMessage,
    addFiles,
    removeItem,
    clearBatch,
    analyzeBatch,
    retryItem
  };
}

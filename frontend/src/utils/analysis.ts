import type { TechnicalValidation, ValidationItem } from "@/types/analysis";

const VALIDATION_CONFIG: Array<{
  key: keyof TechnicalValidation;
  label: string;
  description: string;
}> = [
  {
    key: "formatAllowed",
    label: "Formato permitido",
    description: "Verifica que el formato de archivo cumpla la guia tecnica."
  },
  {
    key: "dimensionsValid",
    label: "Dimensiones validas",
    description: "Confirma que el ancho y alto cumplen el minimo requerido."
  },
  {
    key: "fileSizeValid",
    label: "Peso del archivo",
    description: "Valida que el tamano de archivo este dentro del limite."
  }
];

export function getValidationItems(validation: TechnicalValidation): ValidationItem[] {
  return VALIDATION_CONFIG.map((item) => ({
    ...item,
    ok: validation[item.key]
  }));
}

export function calculateScore(validation: TechnicalValidation): number {
  const values = Object.values(validation);
  const passed = values.filter(Boolean).length;
  return Math.round((passed / values.length) * 100);
}

export function toMegaBytes(sizeKb: number): string {
  return `${(sizeKb / 1024).toFixed(2)} MB`;
}

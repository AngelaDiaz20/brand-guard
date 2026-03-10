"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";

import Layout from "@/components/Layout";
import { SectionCard } from "@/components/ui/SectionCard";

type Rgb = { r: number; g: number; b: number };

type BrandColor = {
  id: string;
  hex: string; // #RRGGBB
  rgb: Rgb;
  name?: string;
};

type BrandLogo = {
  id: string;
  brandName: string;
  fileName: string;
  fileSizeKb: number;
  previewUrl: string;
  dominantColors: string[]; // HEX list
};

type BrandRules = {
  minimumLogoSizePx: number;
  allowedBackgroundColorIds: string[];
  minimumContrastRatio: number;
};

function clampInt(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function isValidHex(hex: string) {
  return /^#[0-9a-fA-F]{6}$/.test(hex);
}

function normalizeHex(hex: string) {
  const trimmed = hex.trim();
  if (trimmed.startsWith("#")) {
    return `#${trimmed.slice(1).toUpperCase()}`;
  }
  return `#${trimmed.toUpperCase()}`;
}

function hexToRgb(hex: string): Rgb | null {
  if (!isValidHex(hex)) {
    return null;
  }
  const raw = hex.slice(1);
  const r = parseInt(raw.slice(0, 2), 16);
  const g = parseInt(raw.slice(2, 4), 16);
  const b = parseInt(raw.slice(4, 6), 16);
  return { r, g, b };
}

function rgbToHex(rgb: Rgb) {
  const toHex = (value: number) => clampInt(value, 0, 255).toString(16).padStart(2, "0");
  return `#${toHex(rgb.r)}${toHex(rgb.g)}${toHex(rgb.b)}`.toUpperCase();
}

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`;
}

function splitHexList(input: string) {
  const raw = input
    .split(/[,\s]+/g)
    .map((item) => item.trim())
    .filter(Boolean);

  const normalized = raw
    .map((item) => normalizeHex(item))
    .filter((item) => isValidHex(item));

  return Array.from(new Set(normalized));
}

function ColorSwatch({ hex }: { hex: string }) {
  return (
    <span
      className="inline-block h-9 w-9 rounded-xl border border-slate-200 shadow-sm"
      style={{ backgroundColor: hex }}
      aria-label={`Muestra ${hex}`}
      title={hex}
    />
  );
}

function FieldLabel({ children }: { children: string }) {
  return (
    <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
      {children}
    </p>
  );
}

export default function LineamientosPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const logosRef = useRef<BrandLogo[]>([]);

  const [colors, setColors] = useState<BrandColor[]>([
    { id: "c1", name: "Marca principal", hex: "#0F172A", rgb: { r: 15, g: 23, b: 42 } },
    { id: "c2", name: "Acento de marca", hex: "#2563EB", rgb: { r: 37, g: 99, b: 235 } },
    { id: "c3", name: "Fondo suave", hex: "#F8FAFC", rgb: { r: 248, g: 250, b: 252 } }
  ]);

  const [editingColorId, setEditingColorId] = useState<string | null>(null);
  const [colorDraft, setColorDraft] = useState<{
    name: string;
    hex: string;
    r: string;
    g: string;
    b: string;
  }>({ name: "", hex: "#", r: "", g: "", b: "" });

  const [newColor, setNewColor] = useState<{
    name: string;
    hex: string;
    r: string;
    g: string;
    b: string;
  }>({ name: "", hex: "#2563EB", r: "37", g: "99", b: "235" });

  const [logos, setLogos] = useState<BrandLogo[]>([]);
  const [logoDraft, setLogoDraft] = useState<{
    brandName: string;
    dominantColorsInput: string;
  }>({ brandName: "", dominantColorsInput: "" });

  const [rules, setRules] = useState<BrandRules>({
    minimumLogoSizePx: 96,
    allowedBackgroundColorIds: ["c3"],
    minimumContrastRatio: 4.5
  });

  useEffect(() => {
    // Keep rules background selections valid if colors are removed.
    setRules((prev) => ({
      ...prev,
      allowedBackgroundColorIds: prev.allowedBackgroundColorIds.filter((id) =>
        colors.some((color) => color.id === id)
      )
    }));
  }, [colors]);

  const allowedBackgroundColors = useMemo(() => {
    const byId = new Map(colors.map((c) => [c.id, c]));
    return rules.allowedBackgroundColorIds.map((id) => byId.get(id)).filter(Boolean) as BrandColor[];
  }, [colors, rules.allowedBackgroundColorIds]);

  const startEditColor = (color: BrandColor) => {
    setEditingColorId(color.id);
    setColorDraft({
      name: color.name ?? "",
      hex: color.hex,
      r: String(color.rgb.r),
      g: String(color.rgb.g),
      b: String(color.rgb.b)
    });
  };

  const cancelEditColor = () => {
    setEditingColorId(null);
    setColorDraft({ name: "", hex: "#", r: "", g: "", b: "" });
  };

  const saveEditColor = () => {
    if (!editingColorId) {
      return;
    }

    const nextHex = normalizeHex(colorDraft.hex);
    const parsedRgb =
      isValidHex(nextHex) ? hexToRgb(nextHex) : null;

    const rgbFromInputs: Rgb = {
      r: clampInt(Number(colorDraft.r), 0, 255),
      g: clampInt(Number(colorDraft.g), 0, 255),
      b: clampInt(Number(colorDraft.b), 0, 255)
    };

    const nextRgb = parsedRgb ?? rgbFromInputs;
    const finalHex = parsedRgb ? nextHex : rgbToHex(nextRgb);

    setColors((prev) =>
      prev.map((c) =>
        c.id === editingColorId
          ? {
              ...c,
              name: colorDraft.name.trim() ? colorDraft.name.trim() : undefined,
              hex: finalHex,
              rgb: nextRgb
            }
          : c
      )
    );
    cancelEditColor();
  };

  const deleteColor = (id: string) => {
    setColors((prev) => prev.filter((c) => c.id !== id));
  };

  const addColor = () => {
    const nextHex = normalizeHex(newColor.hex);
    const parsedRgb = hexToRgb(nextHex);

    const rgbFromInputs: Rgb = {
      r: clampInt(Number(newColor.r), 0, 255),
      g: clampInt(Number(newColor.g), 0, 255),
      b: clampInt(Number(newColor.b), 0, 255)
    };

    const rgb = parsedRgb ?? rgbFromInputs;
    const hex = parsedRgb ? nextHex : rgbToHex(rgb);

    setColors((prev) => [
      ...prev,
      {
        id: uid("color"),
        name: newColor.name.trim() ? newColor.name.trim() : undefined,
        hex,
        rgb
      }
    ]);

    setNewColor({ name: "", hex: "#", r: "", g: "", b: "" });
  };

  const pickLogoFile = () => fileInputRef.current?.click();

  const addLogoFromFile = (file: File) => {
    const previewUrl = URL.createObjectURL(file);
    const dominantColors = splitHexList(logoDraft.dominantColorsInput);

    const brandName = logoDraft.brandName.trim();
    if (!brandName) {
      URL.revokeObjectURL(previewUrl);
      return;
    }

    const logo: BrandLogo = {
      id: uid("logo"),
      brandName,
      fileName: file.name,
      fileSizeKb: Math.round(file.size / 1024),
      previewUrl,
      dominantColors
    };

    setLogos((prev) => [logo, ...prev]);
    setLogoDraft({ brandName: "", dominantColorsInput: "" });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleLogoFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      addLogoFromFile(file);
    }
  };

  const deleteLogo = (id: string) => {
    setLogos((prev) => {
      const found = prev.find((l) => l.id === id);
      if (found) {
        URL.revokeObjectURL(found.previewUrl);
      }
      return prev.filter((l) => l.id !== id);
    });
  };

  useEffect(() => {
    logosRef.current = logos;
  }, [logos]);

  useEffect(() => {
    return () => {
      // Cleanup object URLs on page unmount.
      logosRef.current.forEach((logo) => URL.revokeObjectURL(logo.previewUrl));
    };
  }, []);

  return (
    <Layout title="Lineamientos">
      <div className="space-y-6">
        <SectionCard className="relative overflow-hidden">
          <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                Validacion de marca
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">Lineamientos</h2>
              <p className="mt-1 text-sm text-slate-600">
                Configura colores, logos y reglas. Datos solo en estado local.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              Estado local
            </span>
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-28 -top-28 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_center,rgba(15,23,42,0.10),transparent_62%)]"
          />
        </SectionCard>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <SectionCard>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <FieldLabel>Seccion 1</FieldLabel>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900">Colores de marca</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Administra el set de colores permitidos para validacion.
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-[1fr_140px_1fr]">
                <div>
                  <p className="text-xs font-medium text-slate-600">Nombre (opcional)</p>
                  <input
                    value={newColor.name}
                    onChange={(e) => setNewColor((p) => ({ ...p, name: e.target.value }))}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    placeholder="ej. Primario"
                  />
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-600">HEX</p>
                  <input
                    value={newColor.hex}
                    onChange={(e) => {
                      const hex = e.target.value;
                      const normalized = hex.startsWith("#") ? hex : `#${hex}`;
                      setNewColor((p) => ({ ...p, hex: normalized }));
                      const parsed = hexToRgb(normalizeHex(normalized));
                      if (parsed) {
                        setNewColor((p) => ({
                          ...p,
                          r: String(parsed.r),
                          g: String(parsed.g),
                          b: String(parsed.b)
                        }));
                      }
                    }}
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    placeholder="#RRGGBB"
                  />
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <p className="text-xs font-medium text-slate-600">R</p>
                    <input
                      inputMode="numeric"
                      value={newColor.r}
                      onChange={(e) => setNewColor((p) => ({ ...p, r: e.target.value }))}
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-600">G</p>
                    <input
                      inputMode="numeric"
                      value={newColor.g}
                      onChange={(e) => setNewColor((p) => ({ ...p, g: e.target.value }))}
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-slate-600">B</p>
                    <input
                      inputMode="numeric"
                      value={newColor.b}
                      onChange={(e) => setNewColor((p) => ({ ...p, b: e.target.value }))}
                      className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                      placeholder="0"
                    />
                  </div>
                </div>

                <div className="sm:col-span-3 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <ColorSwatch
                      hex={isValidHex(normalizeHex(newColor.hex)) ? normalizeHex(newColor.hex) : "#FFFFFF"}
                    />
                    <p className="text-xs text-slate-500">
                      Consejo: puedes pegar HEX o editar RGB.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={addColor}
                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                  >
                    Agregar color
                  </button>
                </div>
              </div>

              <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
                <div className="grid grid-cols-[1fr_140px_1fr_160px] gap-0 bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                  <div>Nombre</div>
                  <div>HEX</div>
                  <div>RGB</div>
                  <div className="text-right">Acciones</div>
                </div>

                <ul className="divide-y divide-slate-200 bg-white">
                  {colors.map((color) => {
                    const editing = editingColorId === color.id;
                    const displayName = color.name ?? "Sin nombre";
                    return (
                      <li key={color.id} className="px-4 py-4">
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_140px_1fr_160px] sm:items-center">
                          <div className="flex items-center gap-3">
                            <ColorSwatch hex={color.hex} />
                            <div className="min-w-0">
                              {editing ? (
                                <input
                                  value={colorDraft.name}
                                  onChange={(e) =>
                                    setColorDraft((p) => ({ ...p, name: e.target.value }))
                                  }
                                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                                  placeholder="Nombre del color"
                                />
                              ) : (
                                <p className="truncate text-sm font-semibold text-slate-900">
                                  {displayName}
                                </p>
                              )}
                              <p className="mt-0.5 text-xs text-slate-500">
                                id: {color.id}
                              </p>
                            </div>
                          </div>

                          <div>
                            {editing ? (
                              <input
                                value={colorDraft.hex}
                                onChange={(e) => {
                                  const raw = e.target.value;
                                  const normalized = raw.startsWith("#") ? raw : `#${raw}`;
                                  setColorDraft((p) => ({ ...p, hex: normalized }));
                                  const parsed = hexToRgb(normalizeHex(normalized));
                                  if (parsed) {
                                    setColorDraft((p) => ({
                                      ...p,
                                      r: String(parsed.r),
                                      g: String(parsed.g),
                                      b: String(parsed.b)
                                    }));
                                  }
                                }}
                                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                              />
                            ) : (
                              <p className="font-mono text-sm text-slate-800">{color.hex}</p>
                            )}
                          </div>

                          <div className="grid grid-cols-3 gap-2">
                            {editing ? (
                              <>
                                <input
                                  inputMode="numeric"
                                  value={colorDraft.r}
                                  onChange={(e) =>
                                    setColorDraft((p) => ({ ...p, r: e.target.value }))
                                  }
                                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                                  placeholder="R"
                                />
                                <input
                                  inputMode="numeric"
                                  value={colorDraft.g}
                                  onChange={(e) =>
                                    setColorDraft((p) => ({ ...p, g: e.target.value }))
                                  }
                                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                                  placeholder="G"
                                />
                                <input
                                  inputMode="numeric"
                                  value={colorDraft.b}
                                  onChange={(e) =>
                                    setColorDraft((p) => ({ ...p, b: e.target.value }))
                                  }
                                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                                  placeholder="B"
                                />
                              </>
                            ) : (
                              <>
                                <p className="font-mono text-sm text-slate-700">{color.rgb.r}</p>
                                <p className="font-mono text-sm text-slate-700">{color.rgb.g}</p>
                                <p className="font-mono text-sm text-slate-700">{color.rgb.b}</p>
                              </>
                            )}
                          </div>

                          <div className="flex items-center justify-end gap-2">
                            {editing ? (
                              <>
                                <button
                                  type="button"
                                  onClick={cancelEditColor}
                                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                                >
                                  Cancelar
                                </button>
                                <button
                                  type="button"
                                  onClick={saveEditColor}
                                  className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                                >
                                  Guardar
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  onClick={() => startEditColor(color)}
                                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                                >
                                  Editar
                                </button>
                                <button
                                  type="button"
                                  onClick={() => deleteColor(color.id)}
                                  className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 shadow-sm transition hover:bg-rose-100"
                                >
                                  Eliminar
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <FieldLabel>Seccion 2</FieldLabel>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900">Logos de marca</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Carga logos y guarda metadata en estado local.
                  </p>
                </div>
              </div>

              <div className="mt-5 space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div>
                  <p className="text-xs font-medium text-slate-600">brand_name</p>
                  <input
                    value={logoDraft.brandName}
                    onChange={(e) =>
                      setLogoDraft((p) => ({ ...p, brandName: e.target.value }))
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    placeholder="ej. Sodimac"
                  />
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-600">dominant_colors</p>
                  <input
                    value={logoDraft.dominantColorsInput}
                    onChange={(e) =>
                      setLogoDraft((p) => ({ ...p, dominantColorsInput: e.target.value }))
                    }
                    className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    placeholder="#0F172A, #2563EB"
                  />
                  <p className="mt-2 text-xs text-slate-500">
                    Consejo: pega una lista HEX separada por comas (solo local).
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={pickLogoFile}
                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                    disabled={!logoDraft.brandName.trim()}
                    title={!logoDraft.brandName.trim() ? "Define brand_name primero" : "Subir logo"}
                  >
                    Subir logo
                  </button>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleLogoFileChange}
                  />
                </div>
              </div>

              <div className="mt-5 space-y-3">
                {logos.length === 0 ? (
                  <div className="rounded-2xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
                    Aun no hay logos.
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {logos.map((logo) => (
                      <li
                        key={logo.id}
                        className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
                      >
                        <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-[88px_1fr_auto] sm:items-center">
                          <div className="grid h-20 w-20 place-items-center overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={logo.previewUrl}
                              alt={`Logo de ${logo.brandName}`}
                              className="h-full w-full object-contain p-2"
                            />
                          </div>

                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900">
                              {logo.brandName}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {logo.fileName} • {logo.fileSizeKb} KB
                            </p>

                            <div className="mt-3 flex flex-wrap items-center gap-2">
                              {logo.dominantColors.length ? (
                                logo.dominantColors.map((hex) => (
                                  <span
                                    key={hex}
                                    className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-800"
                                  >
                                    <span
                                      className="h-3 w-3 rounded-full border border-slate-200"
                                      style={{ backgroundColor: hex }}
                                      aria-hidden="true"
                                    />
                                    <span className="font-mono">{hex}</span>
                                  </span>
                                ))
                              ) : (
                                <span className="text-xs text-slate-500">
                                  Sin colores dominantes definidos.
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex justify-end">
                            <button
                              type="button"
                              onClick={() => deleteLogo(logo.id)}
                              className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 shadow-sm transition hover:bg-rose-100"
                            >
                              Eliminar
                            </button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </SectionCard>

            <SectionCard>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <FieldLabel>Seccion 3</FieldLabel>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900">Reglas de marca</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Define reglas para validacion (sin backend por ahora).
                  </p>
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    Tamano minimo del logo
                  </p>
                  <div className="mt-2 flex items-center gap-3">
                    <input
                      type="number"
                      min={0}
                      value={rules.minimumLogoSizePx}
                      onChange={(e) =>
                        setRules((p) => ({
                          ...p,
                          minimumLogoSizePx: Math.max(0, Number(e.target.value))
                        }))
                      }
                      className="w-32 rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    />
                    <span className="text-sm text-slate-600">px</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Se usa para validar la dimension minima del logo renderizado.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    Colores de fondo permitidos
                  </p>
                  <p className="mt-2 text-sm text-slate-600">
                    Selecciona que colores de marca se permiten como fondo.
                  </p>

                  <div className="mt-4 grid grid-cols-1 gap-2">
                    {colors.map((color) => {
                      const checked = rules.allowedBackgroundColorIds.includes(color.id);
                      return (
                        <label
                          key={color.id}
                          className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm"
                        >
                          <div className="flex min-w-0 items-center gap-3">
                            <span
                              className="h-4 w-4 rounded border border-slate-200"
                              style={{ backgroundColor: color.hex }}
                              aria-hidden="true"
                            />
                            <span className="truncate text-sm font-medium text-slate-900">
                              {color.name ?? "Sin nombre"}
                            </span>
                            <span className="font-mono text-xs text-slate-500">{color.hex}</span>
                          </div>
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              const next = e.target.checked;
                              setRules((prev) => ({
                                ...prev,
                                allowedBackgroundColorIds: next
                                  ? Array.from(new Set([...prev.allowedBackgroundColorIds, color.id]))
                                  : prev.allowedBackgroundColorIds.filter((id) => id !== color.id)
                              }));
                            }}
                            className="h-4 w-4 accent-slate-900"
                          />
                        </label>
                      );
                    })}
                  </div>

                  <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                      Seleccionados
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {allowedBackgroundColors.length ? (
                        allowedBackgroundColors.map((c) => (
                          <span
                            key={c.id}
                            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-medium text-slate-800"
                          >
                            <span
                              className="h-3 w-3 rounded-full border border-slate-200"
                              style={{ backgroundColor: c.hex }}
                              aria-hidden="true"
                            />
                            <span className="font-mono">{c.hex}</span>
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-slate-500">
                          No hay colores de fondo seleccionados.
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    Contraste minimo
                  </p>
                  <div className="mt-2 flex items-center gap-3">
                    <input
                      type="number"
                      min={1}
                      step={0.1}
                      value={rules.minimumContrastRatio}
                      onChange={(e) =>
                        setRules((p) => ({
                          ...p,
                          minimumContrastRatio: Math.max(1, Number(e.target.value))
                        }))
                      }
                      className="w-32 rounded-xl border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400"
                    />
                    <span className="text-sm text-slate-600">relacion</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Objetivos tipicos: 3.0 (texto grande) o 4.5 (estandar).
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setRules({
                        minimumLogoSizePx: 96,
                        allowedBackgroundColorIds: [],
                        minimumContrastRatio: 4.5
                      })
                    }
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                  >
                    Restablecer
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      // Local-only: would persist to backend later.
                      console.info("Rules saved (local only):", rules);
                    }}
                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
                  >
                    Guardar reglas
                  </button>
                </div>
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </Layout>
  );
}

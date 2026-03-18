"use client";

import { useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { SectionCard } from "@/components/ui/SectionCard";

interface ScoreCardProps {
  score: number; // 0..100
  passedChecks: number;
  totalChecks: number;
}

export function ScoreCard({ score, passedChecks, totalChecks }: ScoreCardProps) {
  const safeScore = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;

  const mv = useMotionValue(0);
  const rounded = useTransform(mv, (v) => Math.round(v));

  useEffect(() => {
    const controls = animate(mv, safeScore, { duration: 1.1, ease: "easeOut" });
    return () => controls.stop();
  }, [safeScore, mv]);

  // Círculo SVG
  const size = 120;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const progress = (safeScore / 100) * c;

  return (
    <SectionCard className="bg-white">
      <p className="text-sm font-medium text-slate-500">Puntaje general</p>

      <div className="mt-4 flex items-center gap-6">
        {/* CÍRCULO */}
        <div className="relative h-[120px] w-[120px]">
          <svg width={size} height={size} className="-rotate-90">
            {/* Track */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              strokeWidth={stroke}
              className="stroke-slate-200"
            />
            {/* Progress animado */}
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              strokeWidth={stroke}
              strokeLinecap="round"
              className="stroke-blue-600"
              strokeDasharray={c}
              initial={{ strokeDashoffset: c }}
              animate={{ strokeDashoffset: c - progress }}
              transition={{ duration: 1.1, ease: "easeOut" }}
            />
          </svg>

          {/* Número al centro */}
          <div className="absolute inset-0 grid place-items-center">
            <div className="text-center">
              <motion.div className="text-4xl font-bold text-slate-900">
                {rounded}
              </motion.div>
              <div className="-mt-1 text-sm text-slate-500">/ 100</div>
            </div>
          </div>
        </div>

        {/* TEXTO */}
        <div className="flex-1">
          <div className="text-2xl font-semibold text-slate-900">
            {Math.round(safeScore)}%
          </div>
          <p className="mt-1 text-sm text-slate-600">
            {passedChecks} de {totalChecks} validaciones técnicas aprobadas.
          </p>
        </div>
      </div>
    </SectionCard>
  );
}

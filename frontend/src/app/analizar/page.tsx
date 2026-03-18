"use client";

import Layout from "@/components/Layout";
import { AnalyzeAssetView } from "@/features/analysis/AnalyzeAssetView";

export default function AnalizarPage() {
  return (
    <Layout title="Analizar Activo">
      <AnalyzeAssetView />
    </Layout>
  );
}

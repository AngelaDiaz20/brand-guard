"use client";

import Layout from "@/components/Layout";
// Aquí importa el componente que quieres mostrar en lugar del contenido actual
import Analisis from "@/app/page";

export default function AnalizarPage() {
  return (
    <Layout title="Analizar Activo">
      {/* Contenedor principal del dashboard: Sidebar + contenido */}
      <div className="flex min-h-[calc(100vh-64px)]">
        {/* Sidebar se mantiene dentro del Layout */}
        {/* Si tu Layout ya incluye Sidebar, no necesitas agregarlo aquí */}

        {/* Contenido principal */}
        <main className="flex-1 p-6">
          {/* Renderiza el componente que desees */}
          <Analisis />
        </main>
      </div>
    </Layout>
  );
}
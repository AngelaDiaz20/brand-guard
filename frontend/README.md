# Frontend - Next.js + TypeScript + Tailwind

Frontend modular para cargar imagenes, enviarlas al backend FastAPI y mostrar resultados de validacion tecnica.

## Stack

- Next.js (App Router)
- TypeScript
- Tailwind CSS

## Estructura

```text
frontend/
  src/
    app/
      layout.tsx
      page.tsx
      globals.css
    components/
      analysis/
        ProgressScreen.tsx
      results/
        MetadataPanel.tsx
        ResultsScreen.tsx
        ScoreCard.tsx
        ValidationCard.tsx
      ui/
        SectionCard.tsx
      upload/
        UploadArea.tsx
    lib/
      api.ts
    types/
      analysis.ts
    utils/
      analysis.ts
  next.config.ts
  tailwind.config.ts
  tsconfig.json
  postcss.config.mjs
```

## Instalacion

```bash
npm install
```

## Ejecutar en desarrollo

```bash
npm run dev
```

La app queda disponible en `http://localhost:3000`.

## Endpoint backend usado

- `POST http://127.0.0.1:8000/analyze`
  - Content-Type: `multipart/form-data`
  - Campo del archivo: `file`

## Configuracion opcional

Puedes cambiar la URL base del backend con:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Si no se define, se usa `http://127.0.0.1:8000` por defecto.

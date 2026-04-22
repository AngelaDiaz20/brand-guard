# OCR por regiones semánticas (YOLO → OCR → extracción)

## Problema que resuelve

El OCR global tiende a:

- **Mezclar texto de regiones distintas** (campaña + fecha + precios + descripción) por heurísticas de agrupación basadas en cercanía.
- **Incluir texto incidental** dentro de la **fotografía del producto** (etiqueta del envase, textos impresos dentro de la foto), contaminando `brand/description/campaign/unknown`.

## Por qué YOLO ayuda

YOLO permite **detectar regiones semánticas** del layout (por ejemplo `product_photo_area`, `info_card_area`, `price_main_area`), para:

- Ejecutar OCR **solo** en áreas relevantes.
- **Excluir** (o bajar prioridad) del OCR el área `product_photo_area`.
- Mantener trazabilidad: región → OCR por recorte → bloques → campos.

## Clases (v1)

Sugeridas:

- `campaign_area`
- `date_area`
- `product_photo_area`
- `info_card_area`
- `price_main_area`
- `price_secondary_area`
- `sku_area`
- `promo_badge_area`
- `logo_area`

Prioridad mínima recomendada para empezar:

1. `product_photo_area`
2. `info_card_area`
3. `price_main_area`
4. `price_secondary_area`
5. `campaign_area`
6. `date_area`
7. `sku_area`

## Cómo se excluye el texto de `product_photo_area`

En el backend (capa opcional, sin romper el pipeline actual):

1. Se detectan regiones con YOLO (si está habilitado y hay pesos).
2. Se construye una lista `exclude_areas` con los `bbox` de `product_photo_area`.
3. Se ejecuta OCR por recortes (`run_regional_ocr`) sobre regiones comerciales.
4. Al re-proyectar palabras al plano global, se **filtran** palabras cuyo centro cae en `exclude_areas`.

Excepción importante:

- Si una subregión comercial (por ejemplo `price_main_area`) **se superpone** a `product_photo_area`, sus cajas se agregan a `keep_areas` y el filtrado respeta esa excepción (no se excluye el texto del precio).

## Híbrido + fallback (no rompe lo existente)

El flujo actual se mantiene, y se agrega una capa opcional:

- Siempre existe OCR global (compatibilidad / debug / fallback).
- Si YOLO está disponible y detecta `product_photo_area`, se crea además una vista **“masked global”** (bloques reconstruidos sin palabras dentro de la foto).
- Luego se intenta OCR por regiones (semánticas YOLO o regiones propuestas por visión clásica).
- Si el layout regional produce bloques, estos se usan para extracción estructurada; si no, se conserva lo global.

## Debug

`POST /analyze` soporta un flag `debug` (multipart form):

- `debug=true` fuerza a incluir en la respuesta:
  - `ocr.yoloDetections`
  - `ocr.regions`
  - `ocr.regionalOcr`
  - `ocr.incidentalRegionalOcr` (solo `product_photo_area`, para ver el texto incidental sin contaminar extracción)
  - campos con trazabilidad por región (`structuredFields.*.sourceRegionClassName`, etc.)

Ejemplo:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/ruta/a/tu/imagen.png" \
  -F "piece_format=slideshow" \
  -F "debug=true"
```

## Cómo habilitar YOLO

Editar `backend/app/config/excel_validation_config.json`:

- `yolo.enabled`: `true`
- `yolo.model_path`: ruta local a pesos `.pt`
- (opcional) ajustar `conf`, `iou`, `max_det`

Instalar dependencias opcionales:

```bash
pip install -r backend/requirements.txt
pip install -r backend/requirements-yolo.txt
```

## Dataset: formato recomendado y MVP

### Formato recomendado

Para Ultralytics (YOLOv8/v11) el formato más simple es **YOLO TXT**:

- Un archivo `.txt` por imagen.
- Cada línea: `class_id x_center y_center width height` en **coordenadas normalizadas** (0..1).

Más un `data.yaml` con:

- `path`, `train`, `val`
- `names`: lista de clases en orden.

Ultralytics también soporta COCO, pero YOLO TXT suele ser el MVP más rápido.

### Cantidad mínima viable

Para empezar “sin sobreentrenar”:

- **MVP**: ~30–50 ejemplos por clase (con diversidad real de plantillas/fondos).
- **Recomendado**: 150–300 por clase para estabilizar (especialmente `product_photo_area` e `info_card_area`).

### Estrategia para comenzar pequeño

1. Entrenar primero solo:
   - `product_photo_area`, `info_card_area`, `price_main_area`
2. Validar que la extracción deja de contaminarse con texto del envase.
3. Agregar `price_secondary_area`, `campaign_area`, `date_area`, `sku_area`.
4. Mantener una validación rápida con `debug=true` para ver:
   - cajas YOLO
   - texto por región
   - trazabilidad por campo

### Tips anti-overfitting

- Asegurar variedad: distintos productos, iluminación, tamaños, fondos, idiomas/acentos.
- Aumentos moderados: escala, blur leve, brillo/contraste, recortes; evitar aumentos que destruyan tipografía.
- Separar val/test por **campañas** o **familias** (no solo por imagen).


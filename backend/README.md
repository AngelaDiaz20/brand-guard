# Sodimac Technical Validation Backend (Fase 1)

Backend en FastAPI para validación técnica básica de piezas gráficas.

## Alcance de esta fase

- Carga de imagen por `multipart/form-data`
- Validación de tipo de archivo (`JPG`/`PNG`)
- Extracción de metadata con Pillow
- Validación contra reglas técnicas definidas en JSON externo

No incluye aún:

- OCR
- Análisis de color
- Contraste
- Safe area
- Machine learning

## Estructura

```text
backend/
├── app/
│   ├── main.py
│   ├── config/
│   │   └── sodimac_guidelines.json
│   ├── services/
│   │   ├── image_loader.py
│   │   ├── metadata_service.py
│   │   └── guideline_validator.py
│   ├── models/
│   │   └── response_model.py
│   └── utils/
│       └── image_utils.py
├── requirements.txt
└── README.md
```

## Requisitos previos

- Python 3.10 o superior

## 1) Crear entorno virtual

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Ejecutar servidor

```bash
uvicorn app.main:app --reload
```

API docs disponibles en:

- `http://127.0.0.1:8000/docs`

## Endpoint principal

### `POST /analyze`

Recibe una imagen en el campo `file` y retorna metadata + validación técnica.

### Ejemplo con curl

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/ruta/a/tu/imagen.png"
```

### Respuesta esperada (ejemplo)

```json
{
  "meta": {
    "filename": "imagen.png",
    "format": "PNG",
    "width": 1200,
    "height": 1200,
    "aspectRatio": "1:1",
    "fileSizeKb": 420.5,
    "colorMode": "RGB",
    "iccProfile": "Embedded"
  },
  "technicalValidation": {
    "formatAllowed": true,
    "dimensionsValid": true,
    "fileSizeValid": true
  }
}
```

## Configuración dinámica

Las reglas se leen dinámicamente desde:

- `app/config/sodimac_guidelines.json`

Puedes ajustar allí límites de tamaño, dimensiones y formatos permitidos sin cambiar código.

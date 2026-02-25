"""FastAPI entrypoint for Sodimac technical validation service."""

from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware  # 👈 IMPORTANTE

from app.models.response_model import AnalyzeResponse, VisualAnalysisResponse
from app.services.color_analysis_service import extract_dominant_colors
from app.services.guideline_validator import (
    load_guidelines,
    validate_technical_requirements,
)
from app.services.image_loader import load_upload_bytes
from app.services.metadata_service import extract_image_metadata

APP_TITLE = "Sodimac Technical Validation API"
APP_VERSION = "1.0.0"
GUIDELINES_PATH = Path(__file__).resolve().parent / "config" / "sodimac_guidelines.json"

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# 🔹 CORS CONFIGURATION (AÑADIR ESTO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Analyze image metadata and validate technical requirements."""
    file_bytes, file_size_kb = await load_upload_bytes(file)
    metadata = extract_image_metadata(
        image_bytes=file_bytes,
        filename=file.filename or "unknown",
        file_size_kb=file_size_kb,
    )
    dominant_colors = extract_dominant_colors(file_bytes)
    guidelines = load_guidelines(GUIDELINES_PATH)
    validation = validate_technical_requirements(metadata, guidelines)

    return AnalyzeResponse(
        meta=metadata,
        technical_validation=validation,
        visual_analysis=VisualAnalysisResponse(dominant_colors=dominant_colors),
    )

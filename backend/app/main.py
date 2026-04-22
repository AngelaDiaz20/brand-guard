"""FastAPI entrypoint for Sodimac technical validation service."""

from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models.response_model import AnalyzeResponse
from app.services.analysis_service import analyze_upload

APP_TITLE = "Sodimac Technical Validation API"
APP_VERSION = "1.0.0"
GUIDELINES_PATH = Path(__file__).resolve().parent / "config" / "sodimac_guidelines.json"

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    excel_file: UploadFile | None = File(default=None, alias="excel_file"),
    piece_format: str | None = Form(default=None, alias="piece_format"),
    debug: bool = Form(default=False, alias="debug"),
) -> AnalyzeResponse:
    """Analyze image/PDF metadata and validate technical requirements."""
    return await analyze_upload(
        file=file,
        guidelines_path=GUIDELINES_PATH,
        excel_file=excel_file,
        piece_format=piece_format,
        debug=debug,
    )

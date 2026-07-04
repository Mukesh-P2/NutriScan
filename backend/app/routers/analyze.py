"""POST /api/analyze — scan one or more images of a food product."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import AnalysisResult
from app.services import gemini

router = APIRouter(prefix="/api", tags=["analyze"])

MAX_IMAGES = 6
MAX_BYTES = 8 * 1024 * 1024  # 8 MB per image
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(
    images: list[UploadFile] = File(...),
    total_weight: str | None = Form(None),
) -> AnalysisResult:
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required.")
    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"At most {MAX_IMAGES} images per scan.")

    payload: list[tuple[bytes, str]] = []
    for img in images:
        content_type = (img.content_type or "").lower()
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type or 'unknown'}")
        data = await img.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty image file.")
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=400, detail="Image too large (max 8 MB).")
        payload.append((data, content_type))

    try:
        return gemini.analyze_images(payload, total_weight=(total_weight or "").strip() or None)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}")

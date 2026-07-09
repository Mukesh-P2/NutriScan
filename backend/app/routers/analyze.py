"""POST /api/analyze — scan one or more images of a food product."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.deps import get_current_user_optional, rate_limit_ai
from app.models.user import User
from app.schemas import ScanResponse
from app.services import gemini, openfoodfacts
from app.services.nutrition import compute_targets, personal_targets_context

router = APIRouter(prefix="/api", tags=["analyze"])


def _personal_context(user: User | None) -> str | None:
    """Personalize only when a user is logged in AND their profile is complete."""
    if user is None:
        return None
    targets = compute_targets(user.profile)
    return personal_targets_context(targets) if targets.complete else None

MAX_IMAGES = 6
MAX_BYTES = 8 * 1024 * 1024  # 8 MB per image
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@router.post("/analyze", response_model=ScanResponse, dependencies=[Depends(rate_limit_ai)])
async def analyze(
    images: list[UploadFile] = File(...),
    total_weight: str | None = Form(None),
    cross_check: bool = Form(True),
    user: User | None = Depends(get_current_user_optional),
) -> ScanResponse:
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
        result = gemini.analyze_images(
            payload,
            total_weight=(total_weight or "").strip() or None,
            personal_context=_personal_context(user),
        )
    except gemini.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Best-effort: if a barcode was read, cross-check it against Open Food Facts as a HINT.
    # Never let a lookup failure fail the scan, and never block the event loop on the sync call.
    barcode_lookup = None
    if cross_check and result.barcode and result.barcode.strip().isdigit():
        try:
            found = await run_in_threadpool(openfoodfacts.lookup_barcode, result.barcode.strip())
            barcode_lookup = found if found.found else None
        except openfoodfacts.LookupError:
            barcode_lookup = None

    return ScanResponse(**result.model_dump(), barcode_lookup=barcode_lookup)

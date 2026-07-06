"""POST /api/ask — free-form food question, with optional supporting image."""

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from app.deps import get_current_user_optional
from app.models.user import User
from app.schemas import AskResponse
from app.services import gemini
from app.services.nutrition import compute_targets, personal_targets_context

router = APIRouter(prefix="/api", tags=["ask"])

MAX_BYTES = 8 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


def _personal_context(user: User | None) -> str | None:
    if user is None:
        return None
    targets = compute_targets(user.profile)
    return personal_targets_context(targets) if targets.complete else None


@router.post("/ask", response_model=AskResponse)
async def ask(
    question: str = Form(...),
    image: UploadFile | None = None,
    user: User | None = Depends(get_current_user_optional),
) -> AskResponse:
    question = question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    image_payload: tuple[bytes, str] | None = None
    if image is not None:
        content_type = (image.content_type or "").lower()
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type or 'unknown'}")
        data = await image.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=400, detail="Image too large (max 8 MB).")
        if data:
            image_payload = (data, content_type)

    try:
        return gemini.ask_question(question, image_payload, personal_context=_personal_context(user))
    except gemini.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

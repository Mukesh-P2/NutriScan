"""Profile endpoints: read/update the user's profile and compute personalized targets."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_schemas import NutritionTargets, ProfileRead, ProfileUpdate
from app.db import get_db
from app.deps import get_current_user
from app.models.user import Profile, User
from app.schemas import TargetGuidance
from app.services import gemini
from app.services.nutrition import compute_targets, guidance_facts

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileRead)
def get_profile(current: User = Depends(get_current_user)) -> Profile:
    # An empty Profile serializes to all-null fields, which the form handles fine.
    return current.profile or Profile()


@router.put("", response_model=ProfileRead)
def update_profile(
    payload: ProfileUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = current.profile
    if profile is None:
        profile = Profile(user_id=current.id)
        db.add(profile)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/targets", response_model=NutritionTargets)
def get_targets(current: User = Depends(get_current_user)) -> NutritionTargets:
    return compute_targets(current.profile)


@router.get("/guidance", response_model=TargetGuidance)
def get_guidance(current: User = Depends(get_current_user)) -> TargetGuidance:
    """AI guidance grounded in the user's computed targets.

    The numbers stay deterministic (compute_targets); the AI only advises around the exact
    figures we pass it, so it can't fabricate health-critical values.
    """
    targets = compute_targets(current.profile)
    try:
        return gemini.target_guidance(guidance_facts(current.profile, targets))
    except gemini.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

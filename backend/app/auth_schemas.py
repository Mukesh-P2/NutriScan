"""Pydantic request/response models for auth & profile endpoints.

Kept separate from ``schemas.py`` (which defines the Gemini structured-output models)
so the AI and account concerns don't bleed into each other.
"""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import ActivityLevel, Goal, Sex


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=120)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    sex: Sex | None = None
    height_cm: float | None = Field(default=None, ge=50, le=260)
    weight_kg: float | None = Field(default=None, ge=2, le=500)
    activity_level: ActivityLevel | None = None
    goal: Goal | None = None


class ProfileRead(ProfileUpdate):
    model_config = {"from_attributes": True}


class NutrientTarget(BaseModel):
    name: str
    amount: float
    unit: str


class NutritionTargets(BaseModel):
    """A user's personalized daily targets, or generic adult defaults if the profile is incomplete."""

    calories: int
    complete: bool = Field(description="False when the profile is missing fields; targets are then generic defaults")
    basis: str = Field(description="Human-readable explanation of how the targets were derived")
    targets: list[NutrientTarget]

"""Pydantic models for API responses. These double as Gemini structured-output schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    healthy = "healthy"
    moderate = "moderate"
    unhealthy = "unhealthy"


class NutrientStatus(str, Enum):
    good = "good"
    high = "high"
    low = "low"
    neutral = "neutral"


class Nutrient(BaseModel):
    name: str = Field(description="Nutrient name, e.g. Protein, Sugar, Sodium")
    amount_per_serving: str = Field(description="Amount in one serving with unit, e.g. '5g'")
    daily_reference: str = Field(description="Recommended daily amount for a typical adult, e.g. '50g'")
    percent_of_daily: int = Field(description="Percent of the daily reference this serving provides (0-100+)")
    status: NutrientStatus = Field(description="good = healthy level, high = too much, low = little, neutral")


class AnalysisResult(BaseModel):
    """The structured verdict returned for a scanned food product."""

    product_name: str = Field(description="Best-guess product name, or a natural food name like 'Apple'")
    barcode: str | None = Field(default=None, description="Barcode digits if visible in any image, else null")
    verdict: Verdict
    score: int = Field(description="Overall healthiness score 0-100 (higher is healthier)")
    summary: str = Field(description="One or two sentence plain-language summary")
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list, description="Actionable tips for the consumer")
    key_nutrients: list[Nutrient] = Field(default_factory=list)
    recommended_serving: str = Field(description="Sensible serving size, e.g. '≈30g per serving'")
    max_per_day: str = Field(description="Upper guidance, e.g. 'up to 2 servings'")
    daily_context_note: str = Field(description="Baseline assumption, e.g. 'Assumes a typical adult (~2000 kcal/day).'")
    total_weight: str | None = Field(
        default=None,
        description="Total pack weight considered (from the user or the label), e.g. '90g'. Null if unknown.",
    )
    servings_in_pack: float | None = Field(
        default=None,
        description="How many servings the full pack contains, if total weight is known. Null otherwise.",
    )
    whole_pack_context: str | None = Field(
        default=None,
        description=(
            "If total weight is known: the whole-pack impact and how much of the pack to eat, e.g. "
            "'The full 90g pack is ~1.8 servings (~504 kcal) and covers ~76% of your daily saturated-fat limit; "
            "eat about half the pack in one sitting.' Null if total weight is unknown."
        ),
    )
    contains_trans_fat: bool = Field(default=False, description="True if trans fat > 0 or partially hydrogenated oils listed")
    is_ultra_processed: bool = Field(default=False, description="True if ultra-processed / long additive list")
    contains_palm_oil: bool = Field(default=False, description="True if palm oil or refined/hydrogenated oils listed")
    main_ingredient_refined_grain: bool = Field(default=False, description="True if a refined grain is the main ingredient")
    has_ingredients: bool = Field(description="False for whole/natural foods with no ingredient label")
    missing_info: list[str] = Field(
        default_factory=list,
        description="Key data still missing (e.g. 'net_weight', 'ingredients'); hints the user to add another image",
    )


class AskResponse(BaseModel):
    """Answer to a free-form food question."""

    answer: str = Field(description="Conversational answer to the question")
    food_name: str | None = Field(default=None, description="Food the question is about, if identifiable")
    is_natural_food: bool = Field(default=False, description="True if it's a basic whole food with no ingredient list")
    benefits: list[str] = Field(default_factory=list)
    nutrients: list[Nutrient] = Field(default_factory=list)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

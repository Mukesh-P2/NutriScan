"""Request/response schemas for consumption tracking."""

from pydantic import BaseModel, Field

from app.schemas import ServingNutrition, Verdict


class ConsumeInput(BaseModel):
    """What the client sends to preview or log an item. Nutrition is PER SERVING."""

    product_name: str = Field(min_length=1, max_length=200)
    servings: float = Field(default=1.0, gt=0, le=50)
    nutrition: ServingNutrition
    product_verdict: Verdict | None = Field(default=None, description="The product's own health verdict, if known")
    product_score: int | None = Field(default=None, ge=0, le=100, description="The product's own 0-100 score, if known")


class NutrientEffect(BaseModel):
    """How consuming this item affects one nutrient relative to the daily target."""

    name: str
    kind: str = Field(description="beneficial | budget | limit")
    unit: str
    target: float
    consumed_before: float
    adds: float
    remaining_after: float = Field(description="target − (consumed_before + adds); negative means over")
    status: str = Field(description="fills | completes | met | ok | near | over | pushes_over")
    message: str


class ConsumptionRecommendation(BaseModel):
    """The 'should I eat this now?' answer — deterministic, based on remaining targets."""

    product_name: str
    servings: float
    targets_complete: bool = Field(description="False if profile incomplete; targets are generic defaults")

    daily_fit: str = Field(description="good | ok | avoid — fit with what's left of your day")
    fit_headline: str

    general: str = Field(description="generally_fine | moderation | limit — the product's own healthiness")
    general_message: str

    effects: list[NutrientEffect]
    current_achievement_pct: int
    projected_achievement_pct: int


class NutrientProgress(BaseModel):
    name: str
    kind: str
    unit: str
    consumed: float
    target: float
    remaining: float = Field(description="target − consumed; may be negative")
    percent: int = Field(description="consumed/target as a percent (display, capped)")
    over: bool


class ConsumptionEntry(BaseModel):
    id: int
    product_name: str
    servings: float
    calories: float
    consumed_at: str


class DailyProgress(BaseModel):
    date: str
    targets_complete: bool
    achievement_pct: int = Field(description="Overall progress toward the day's targets (0-100)")
    calories_consumed: float
    calories_target: int
    nutrients: list[NutrientProgress]
    entries: list[ConsumptionEntry]


class DaySummary(BaseModel):
    date: str
    achievement_pct: int
    calories_consumed: float
    calories_target: int
    entries: int


class HistoryResponse(BaseModel):
    days: list[DaySummary]


class WeeklyAverages(BaseModel):
    """Average daily intake over a rolling window (deterministic; unlogged days count as 0)."""

    days: int = Field(description="Window size in days")
    days_logged: int = Field(description="Days in the window with at least one logged item")
    targets_complete: bool = Field(description="False if profile incomplete; targets are generic defaults")
    avg_achievement_pct: int = Field(description="Mean daily achievement % across the window")
    avg_calories: float = Field(description="Mean daily calories consumed across the window")
    calories_target: int
    nutrients: list[NutrientProgress] = Field(description="Per-nutrient average consumed vs. target")

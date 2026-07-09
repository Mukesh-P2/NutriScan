"""Builders for test fixtures — profiles and analysis results with sensible defaults."""

from app.models.user import ActivityLevel, Goal, Profile, Sex
from app.schemas import AnalysisResult, Nutrient, NutrientStatus, Verdict


def make_profile(**over) -> Profile:
    """A complete male profile (unpersisted) unless fields are overridden."""
    fields = dict(
        age=30,
        sex=Sex.male,
        height_cm=180.0,
        weight_kg=75.0,
        activity_level=ActivityLevel.moderate,
        goal=Goal.maintain,
    )
    fields.update(over)
    return Profile(**fields)


def make_nutrient(name: str, percent: int, status: NutrientStatus = NutrientStatus.neutral) -> Nutrient:
    return Nutrient(
        name=name,
        amount_per_serving="0g",
        daily_reference="0g",
        percent_of_daily=percent,
        status=status,
    )


def make_analysis(**over) -> AnalysisResult:
    """A minimal valid AnalysisResult; override any field for the scenario under test."""
    fields = dict(
        product_name="Test",
        verdict=Verdict.moderate,
        score=50,
        summary="s",
        recommended_serving="30g",
        max_per_day="2 servings",
        daily_context_note="note",
        has_ingredients=True,
        key_nutrients=[],
    )
    fields.update(over)
    return AnalysisResult(**fields)

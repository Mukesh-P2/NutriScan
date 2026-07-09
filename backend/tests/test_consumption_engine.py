"""The deterministic consumption engine (intake vs. targets)."""

from app.schemas import ServingNutrition, Verdict
from app.services.consumption import (
    achievement_pct,
    nutrition_totals,
    recommend,
    weekly_averages,
)
from app.services.nutrition import compute_targets
from tests.helpers import make_profile

TVALS = {
    "calories": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 67,
    "fiber_g": 28, "sugar_g": 50, "saturated_fat_g": 22, "sodium_mg": 2300,
}


def test_achievement_zero_when_nothing_eaten():
    assert achievement_pct(TVALS, {}) == 0


def test_achievement_full_goals_no_limits():
    consumed = {"calories": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 67, "fiber_g": 28}
    assert achievement_pct(TVALS, consumed) == 100


def test_nutrition_totals_scale_by_servings():
    totals = nutrition_totals(ServingNutrition(calories=100, protein_g=5), 2)
    assert totals["calories"] == 200
    assert totals["protein_g"] == 10


def test_recommend_good_pick_fills_protein():
    targets = compute_targets(make_profile())
    rec = recommend(targets, {}, ServingNutrition(protein_g=20), 1, "Yogurt", Verdict.healthy)
    assert rec.daily_fit == "good"
    assert any(e.name == "Protein" for e in rec.effects)


def test_recommend_avoids_over_limit():
    targets = compute_targets(make_profile())
    rec = recommend(targets, {}, ServingNutrition(sodium_mg=5000), 1, "Chips", Verdict.unhealthy)
    assert rec.daily_fit == "avoid"


def test_weekly_averages_over_window():
    targets = compute_targets(make_profile())
    days = [{"calories": 2000, "protein_g": 100}, {"calories": 0}]
    wk = weekly_averages(targets, days, days_logged=1)
    assert wk.days == 2
    assert wk.avg_calories == 1000.0

"""Deterministic daily-target math (Mifflin–St Jeor + RDA splits)."""

from app.models.user import ActivityLevel, Goal, Sex
from app.services.nutrition import bmi, compute_targets
from tests.helpers import make_profile


def test_incomplete_profile_returns_generic_defaults():
    t = compute_targets(None)
    assert t.complete is False
    assert t.calories == 2000


def test_known_male_matches_mifflin_st_jeor():
    # BMR = 10*75 + 6.25*180 - 5*30 + 5 = 1730; TDEE = 1730 * 1.55 (moderate) = 2681.5 → 2682.
    t = compute_targets(make_profile())
    assert t.complete is True
    assert t.calories == 2682


def test_goal_deltas_shift_calories_by_1000():
    lose = compute_targets(make_profile(goal=Goal.lose)).calories
    gain = compute_targets(make_profile(goal=Goal.gain)).calories
    assert gain - lose == 1000  # +500 vs -500 kcal


def test_calorie_floor_never_below_1200():
    t = compute_targets(
        make_profile(
            sex=Sex.female, age=20, height_cm=150, weight_kg=40,
            activity_level=ActivityLevel.sedentary, goal=Goal.lose,
        )
    )
    assert t.calories == 1200


def test_bmi_computed_and_none_when_missing():
    assert bmi(make_profile(height_cm=180, weight_kg=75)) == 23.1
    assert bmi(None) is None


def test_protein_scales_with_body_weight():
    protein = next(x for x in compute_targets(make_profile(weight_kg=75)).targets if x.name == "Protein")
    assert protein.amount == 120  # 1.6 g/kg * 75 kg

"""Personalized daily nutrition targets.

Calories via Mifflin–St Jeor BMR × activity factor, adjusted for goal; macro/micro
targets derived from calories (and body weight for protein). This is the single source
of "what does this user need per day" — consumption tracking (roadmap #3) will subtract
logged intake from these to show consumed-vs-remaining.
"""

from app.auth_schemas import NutrientTarget, NutritionTargets
from app.models.user import ActivityLevel, Goal, Profile, Sex

_ACTIVITY_FACTOR = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.light: 1.375,
    ActivityLevel.moderate: 1.55,
    ActivityLevel.active: 1.725,
    ActivityLevel.very_active: 1.9,
}
_GOAL_KCAL_DELTA = {Goal.lose: -500, Goal.maintain: 0, Goal.gain: 500}

_REQUIRED_FIELDS = ("age", "sex", "height_cm", "weight_kg", "activity_level")
_DEFAULT_CALORIES = 2000
_MIN_CALORIES = 1200  # floor so aggressive deficits never produce unsafe targets


def _targets_for(calories: int, weight_kg: float | None) -> list[NutrientTarget]:
    # Protein from body weight when known (1.6 g/kg), else 20% of calories.
    protein_g = round(1.6 * weight_kg) if weight_kg else round(calories * 0.20 / 4)
    return [
        NutrientTarget(name="Protein", amount=protein_g, unit="g"),
        NutrientTarget(name="Carbohydrate", amount=round(calories * 0.50 / 4), unit="g"),
        NutrientTarget(name="Fat", amount=round(calories * 0.30 / 9), unit="g"),
        NutrientTarget(name="Fiber", amount=round(14 * calories / 1000), unit="g"),
        NutrientTarget(name="Added sugar", amount=round(calories * 0.10 / 4), unit="g"),
        NutrientTarget(name="Saturated fat", amount=round(calories * 0.10 / 9), unit="g"),
        NutrientTarget(name="Sodium", amount=2300, unit="mg"),
    ]


def compute_targets(profile: Profile | None) -> NutritionTargets:
    if profile and all(getattr(profile, f) is not None for f in _REQUIRED_FIELDS):
        base = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age
        bmr = base + (5 if profile.sex == Sex.male else -161)
        tdee = bmr * _ACTIVITY_FACTOR[profile.activity_level]
        goal = profile.goal or Goal.maintain
        calories = max(_MIN_CALORIES, round(tdee + _GOAL_KCAL_DELTA[goal]))
        basis = (
            f"Mifflin–St Jeor for {profile.sex.value}, {profile.age}y, "
            f"{profile.height_cm:g} cm, {profile.weight_kg:g} kg, "
            f"{profile.activity_level.value.replace('_', ' ')} activity, goal: {goal.value}."
        )
        return NutritionTargets(
            calories=calories, complete=True, basis=basis,
            targets=_targets_for(calories, profile.weight_kg),
        )

    return NutritionTargets(
        calories=_DEFAULT_CALORIES,
        complete=False,
        basis="Generic adult defaults (~2000 kcal/day). Complete your profile for personalized targets.",
        targets=_targets_for(_DEFAULT_CALORIES, None),
    )


def bmi(profile: Profile | None) -> float | None:
    """Body-mass index, computed deterministically (never left to the AI)."""
    if profile and profile.height_cm and profile.weight_kg:
        return round(profile.weight_kg / (profile.height_cm / 100) ** 2, 1)
    return None


def guidance_facts(profile: Profile | None, targets: NutritionTargets) -> str:
    """Plain-text facts handed to the AI. Every number here is authoritative — the prompt
    forbids the model from changing any of them."""
    lines: list[str] = []
    if targets.complete and profile:
        goal = (profile.goal or Goal.maintain).value
        lines.append(
            f"Profile: {profile.sex.value}, age {profile.age}, height {profile.height_cm:g} cm, "
            f"weight {profile.weight_kg:g} kg, activity {profile.activity_level.value.replace('_', ' ')}, "
            f"goal {goal}."
        )
        person_bmi = bmi(profile)
        if person_bmi is not None:
            lines.append(f"BMI: {person_bmi} (already computed — do not recalculate).")
    else:
        lines.append(
            "Profile is incomplete, so the targets below are GENERIC adult defaults, not personalized. "
            "Make this clear in your guidance."
        )

    lines.append(f"Daily calorie target: {targets.calories} kcal (FIXED — do not change).")
    lines.append("Daily nutrient targets (FIXED — do not change):")
    lines += [f"- {t.name}: {t.amount:g} {t.unit}" for t in targets.targets]
    lines.append(f"How these were derived: {targets.basis}")
    return "\n".join(lines)


def personal_targets_context(targets: NutritionTargets) -> str:
    """Context injected into scan/ask so the AI tailors advice to the signed-in user.

    Deliberately scoped: the AI may personalize `tips` and the `daily_context_note`, but must
    keep each nutrient's daily_reference / percent_of_daily on STANDARD adult references so the
    tuned deterministic score stays stable and comparable.
    """
    lines = [
        "PERSONALIZATION — the signed-in user's OWN daily targets (already calculated):",
        f"- Calories: {targets.calories} kcal",
    ]
    lines += [f"- {t.name}: {t.amount:g} {t.unit}" for t in targets.targets]
    lines.append(
        "Personalize your response to help them meet these targets and their goal: tailor your free-text "
        "guidance (and, where your output schema has them, `tips` and `daily_context_note`) and reference "
        "THEIR calorie target rather than a generic ~2000 kcal. "
        "IMPORTANT: if your output includes per-nutrient daily_reference / percent_of_daily, keep those on "
        "STANDARD adult reference values — do NOT recompute them against the personal targets. Only the "
        "free-text guidance should reflect the personalization."
    )
    return "\n".join(lines)

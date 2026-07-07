"""Consumption engine — all deterministic (health-critical numbers are never guessed).

Given a user's daily targets, what they've already eaten today, and a candidate item, this
module computes:
  * per-nutrient effects + human messages ("fills your remaining protein", "pushes you over
    your sodium limit"),
  * an overall daily-fit verdict (good / ok / avoid),
  * an overall achievement % toward the day's targets.

Canonical nutrient keys line up 1:1 with NutritionTargets so nothing is parsed from strings.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.auth_schemas import NutritionTargets
from app.config import settings
from app.consumption_schemas import (
    ConsumptionRecommendation,
    DailyProgress,
    NutrientEffect,
    NutrientProgress,
    WeeklyAverages,
)
from app.schemas import ServingNutrition, Verdict

# canonical key -> (display name, unit, role)
#   beneficial = aim to reach the target (more is better, up to it)
#   budget     = aim to hit but not exceed (energy / macros)
#   limit      = aim to stay under (cap)
_META: dict[str, tuple[str, str, str]] = {
    "calories": ("Calories", "kcal", "budget"),
    "protein_g": ("Protein", "g", "beneficial"),
    "carbs_g": ("Carbohydrate", "g", "budget"),
    "fat_g": ("Fat", "g", "budget"),
    "fiber_g": ("Fiber", "g", "beneficial"),
    "sugar_g": ("Sugars", "g", "limit"),
    "saturated_fat_g": ("Saturated fat", "g", "limit"),
    "sodium_mg": ("Sodium", "mg", "limit"),
}

# NutritionTargets.targets carries these display names → map back to canonical keys.
_TARGET_NAME_TO_KEY = {
    "Protein": "protein_g",
    "Carbohydrate": "carbs_g",
    "Fat": "fat_g",
    "Fiber": "fiber_g",
    "Added sugar": "sugar_g",
    "Saturated fat": "saturated_fat_g",
    "Sodium": "sodium_mg",
}

_GOAL_KEYS = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g")  # completion drives progress
_LIMIT_KEYS = ("sugar_g", "saturated_fat_g", "sodium_mg")  # overage penalizes progress
_NEAR_FRACTION = 0.85  # ≥85% of a limit → "getting close"
_OVER_TOLERANCE = 1.10  # >110% of a limit/budget → serious


def local_today() -> date:
    """Current calendar day in the configured app timezone (falls back to UTC on a bad name).

    This is the single source of "what day is it" for tracking — used at both write time
    (bucketing a logged item) and read time (today/history/weekly), so the day boundary stays
    consistent instead of being hardwired to UTC in several places.
    """
    try:
        tz = ZoneInfo(settings.app_timezone)
    except Exception:
        tz = timezone.utc
    return datetime.now(tz).date()


def target_values(targets: NutritionTargets) -> dict[str, float]:
    """Flatten NutritionTargets into {canonical_key: amount}."""
    values: dict[str, float] = {"calories": float(targets.calories)}
    for t in targets.targets:
        key = _TARGET_NAME_TO_KEY.get(t.name)
        if key:
            values[key] = float(t.amount)
    return values


def nutrition_totals(nutrition: ServingNutrition, servings: float) -> dict[str, float]:
    """Per-serving nutrition × servings → totals dict keyed by canonical key."""
    return {key: float(getattr(nutrition, key, 0.0)) * servings for key in _META}


def _round(x: float) -> float:
    return round(x, 1)


def achievement_pct(tvals: dict[str, float], consumed: dict[str, float]) -> int:
    """Overall progress toward the day's targets (0-100).

    Base = mean completion of the goal nutrients (calories/protein/carbs/fat/fiber), each capped
    at 100%. Penalty = mean overage across the limit nutrients (and calories), which drags the
    score down when you blow past a cap. Transparent and deterministic.
    """
    completions = [min(consumed.get(k, 0.0) / tvals[k], 1.0) for k in _GOAL_KEYS if tvals.get(k)]
    base = sum(completions) / len(completions) if completions else 0.0

    overages = []
    for k in (*_LIMIT_KEYS, "calories"):
        t = tvals.get(k)
        if t:
            overages.append(min(max(0.0, (consumed.get(k, 0.0) - t) / t), 1.0))
    penalty = sum(overages) / len(overages) if overages else 0.0

    return round(max(0.0, min(1.0, base - 0.5 * penalty)) * 100)


def _effect(key: str, target: float, before: float, adds: float) -> NutrientEffect:
    name, unit, kind = _META[key]
    after = before + adds
    remaining_after = target - after
    remaining_before = target - before

    if kind == "beneficial":
        if before >= target:
            status = "met"
            msg = f"You've already met your {name.lower()} goal ({_round(before)}/{_round(target)} {unit}); extra is usually fine."
        elif after >= target:
            status = "completes"
            msg = f"Completes your {name.lower()} goal — adds {_round(adds)} {unit}, and you needed {_round(remaining_before)} {unit}. 🎉"
        else:
            status = "fills"
            msg = f"Helps fill your {name.lower()}: adds {_round(adds)} {unit}, {_round(remaining_after)} {unit} still left after."
    elif kind == "limit":
        if before >= target:
            status = "over"
            msg = f"You've already reached your {name.lower()} limit ({_round(before)}/{_round(target)} {unit}); this adds {_round(adds)} {unit} more."
        elif after > target:
            status = "pushes_over"
            msg = f"Pushes you over your {name.lower()} limit by {_round(after - target)} {unit}."
        elif after >= _NEAR_FRACTION * target:
            status = "near"
            msg = f"Gets you close to your {name.lower()} limit ({_round(after)}/{_round(target)} {unit})."
        else:
            status = "ok"
            msg = f"Fine on {name.lower()} ({_round(after)}/{_round(target)} {unit})."
    else:  # budget
        if before >= target:
            status = "over"
            msg = f"You've already met your {name.lower()} target; this adds {_round(adds)} {unit} over."
        elif after > target:
            status = "pushes_over"
            msg = f"Would put you {_round(after - target)} {unit} over your {name.lower()} target."
        else:
            status = "fills"
            msg = f"Fits your remaining {name.lower()} ({_round(remaining_after)} {unit} left after)."

    return NutrientEffect(
        name=name, kind=kind, unit=unit, target=_round(target), consumed_before=_round(before),
        adds=_round(adds), remaining_after=_round(remaining_after), status=status, message=msg,
    )


_GENERAL = {
    Verdict.healthy: ("generally_fine", "Generally a healthy choice — no problem eating this."),
    Verdict.moderate: ("moderation", "Fine occasionally, but best in moderation."),
    Verdict.unhealthy: ("limit", "Generally an unhealthy product — best kept to a treat."),
}


def recommend(
    targets: NutritionTargets,
    consumed: dict[str, float],
    nutrition: ServingNutrition,
    servings: float,
    product_name: str,
    product_verdict: Verdict | None,
) -> ConsumptionRecommendation:
    tvals = target_values(targets)
    adds = nutrition_totals(nutrition, servings)

    # Only reason about nutrients this item ACTUALLY contributes — an item with 0 fiber shouldn't
    # be described as "filling your fiber", and a nutrient you're already over on isn't this item's
    # fault unless it adds some.
    active = [k for k in _META if tvals.get(k) and adds.get(k, 0.0) > 0]
    effects = [_effect(k, tvals[k], consumed.get(k, 0.0), adds[k]) for k in active]

    # Daily-fit verdict from the limit/budget pressure this item creates.
    serious = 0  # blows a cap by >10%
    mild = 0  # nudges over a cap
    for key in active:
        if key not in _LIMIT_KEYS and key != "calories":
            continue
        after = consumed.get(key, 0.0) + adds[key]
        if after > tvals[key] * _OVER_TOLERANCE:
            serious += 1
        elif after > tvals[key]:
            mild += 1

    # Positive framing: which beneficial goals does it help fill?
    fills = [e.name.lower() for e in effects if e.kind == "beneficial" and e.status in ("fills", "completes")]
    over_names = [e.name.lower() for e in effects if e.status in ("over", "pushes_over")]

    if not active:
        daily_fit = "ok"
        headline = "No per-serving nutrition was available for this item, so its daily fit can't be scored — check the label."
    elif serious:
        daily_fit = "avoid"
        headline = f"🔴 Better to skip or have less — this pushes your {', '.join(over_names)} well over budget for today."
    elif mild:
        daily_fit = "ok"
        watch = ", ".join(over_names) or "your limits"
        extra = f" It does help with your {', '.join(fills)}." if fills else ""
        headline = f"🟡 OK in moderation — keep an eye on {watch}.{extra}"
    else:
        daily_fit = "good"
        if fills:
            headline = f"✅ Good pick for today — it helps fill your remaining {', '.join(fills)}."
        else:
            headline = "✅ Fits comfortably within what's left of your day."

    general, general_msg = _GENERAL.get(product_verdict, ("moderation", "Enjoy sensibly as part of a balanced day."))

    projected = {k: consumed.get(k, 0.0) + adds.get(k, 0.0) for k in _META}
    return ConsumptionRecommendation(
        product_name=product_name,
        servings=servings,
        targets_complete=targets.complete,
        daily_fit=daily_fit,
        fit_headline=headline,
        general=general,
        general_message=general_msg,
        effects=effects,
        current_achievement_pct=achievement_pct(tvals, consumed),
        projected_achievement_pct=achievement_pct(tvals, projected),
    )


def daily_progress(targets: NutritionTargets, consumed: dict[str, float], entries) -> DailyProgress:
    """Build the day's progress view. `entries` is a list of ConsumptionEntry (already shaped)."""
    tvals = target_values(targets)
    nutrients = []
    for key, (name, unit, kind) in _META.items():
        if key == "calories" or not tvals.get(key):
            continue
        target = tvals[key]
        eaten = consumed.get(key, 0.0)
        nutrients.append(
            NutrientProgress(
                name=name, kind=kind, unit=unit, consumed=_round(eaten), target=_round(target),
                remaining=_round(target - eaten), percent=round(min(eaten / target, 2.0) * 100),
                over=eaten > target,
            )
        )

    return DailyProgress(
        date=local_today().isoformat(),
        targets_complete=targets.complete,
        achievement_pct=achievement_pct(tvals, consumed),
        calories_consumed=_round(consumed.get("calories", 0.0)),
        calories_target=targets.calories,
        nutrients=nutrients,
        entries=entries,
    )


def weekly_averages(
    targets: NutritionTargets,
    daily_consumed: list[dict[str, float]],
    days_logged: int,
) -> WeeklyAverages:
    """Average daily intake over a window. `daily_consumed` has one consumed-dict per day in the
    window (0-filled for days with no entries), so the average reflects real calendar days."""
    tvals = target_values(targets)
    n = len(daily_consumed) or 1
    avg = {key: sum(day.get(key, 0.0) for day in daily_consumed) / n for key in _META}

    nutrients = []
    for key, (name, unit, kind) in _META.items():
        if key == "calories" or not tvals.get(key):
            continue
        target = tvals[key]
        eaten = avg[key]
        nutrients.append(
            NutrientProgress(
                name=name, kind=kind, unit=unit, consumed=_round(eaten), target=_round(target),
                remaining=_round(target - eaten), percent=round(min(eaten / target, 2.0) * 100),
                over=eaten > target,
            )
        )

    avg_achievement = round(sum(achievement_pct(tvals, day) for day in daily_consumed) / n)
    return WeeklyAverages(
        days=len(daily_consumed),
        days_logged=days_logged,
        targets_complete=targets.complete,
        avg_achievement_pct=avg_achievement,
        avg_calories=_round(avg.get("calories", 0.0)),
        calories_target=targets.calories,
        nutrients=nutrients,
    )

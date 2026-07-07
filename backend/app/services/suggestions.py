"""Food suggestions — recommend foods to fill the day's REMAINING nutrient gaps.

Deterministic part: the remaining gaps come straight from the consumption engine (targets −
intake). The AI only chooses which foods fill them — it is handed the fixed numbers as frozen
facts and forbidden from changing them (same design principle as target guidance).
"""

from app.consumption_schemas import DailyProgress
from app.schemas import FoodSuggestions
from app.services import gemini


def _facts(progress: DailyProgress, country: str | None, goal: str | None, recent_foods: list[str]) -> str:
    """Serialize today's remaining gaps into the frozen fact block handed to the model."""
    lines: list[str] = []
    if not progress.targets_complete:
        lines.append(
            "NOTE: the user's profile is incomplete, so these are GENERIC adult targets, not personalized. "
            "Make that clear in your summary."
        )
    if goal:
        lines.append(f"Goal: {goal}.")

    cal_remaining = round(progress.calories_target - progress.calories_consumed, 1)
    lines.append(
        f"Calories: {progress.calories_consumed:g} of {progress.calories_target} kcal eaten "
        f"({cal_remaining:g} kcal remaining)."
    )

    need = [n for n in progress.nutrients if n.kind in ("beneficial", "budget") and n.remaining > 0]
    limits = [n for n in progress.nutrients if n.kind == "limit"]

    if need:
        lines.append("Still NEEDS today (aim to fill these — the numbers are FIXED):")
        lines += [f"- {n.name}: {n.remaining:g} {n.unit} remaining (of {n.target:g} {n.unit})." for n in need]
    else:
        lines.append("All beneficial/energy targets are essentially met for today.")

    if limits:
        lines.append("Limits so far today (do NOT push these over):")
        lines += [
            f"- {n.name}: {n.consumed:g} of {n.target:g} {n.unit}"
            + (" — already OVER." if n.over else f" ({n.remaining:g} {n.unit} left).")
            for n in limits
        ]

    if recent_foods:
        lines.append("Recently eaten today (offer variety, don't just repeat): " + ", ".join(recent_foods[:8]) + ".")
    if country:
        lines.append(f"Country (prefer locally available foods): {country}.")

    return "\n".join(lines)


def suggest(
    progress: DailyProgress,
    country: str | None = None,
    goal: str | None = None,
    recent_foods: list[str] | None = None,
) -> FoodSuggestions:
    """Ask the model for foods that fill the remaining gaps described by `progress`."""
    return gemini.suggest_foods(_facts(progress, country, goal, recent_foods or []))

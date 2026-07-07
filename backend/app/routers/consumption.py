"""Consumption tracking endpoints (auth required).

preview  → 'should I eat this now?' given what's left of the day (no persistence)
log      → record it and return the updated day
today    → the current day's progress + entries
history  → per-day achievement for the last N days
DELETE   → undo an entry
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.consumption_schemas import (
    ConsumeInput,
    ConsumptionEntry,
    ConsumptionRecommendation,
    DailyProgress,
    DaySummary,
    HistoryResponse,
    WeeklyAverages,
)
from app.db import get_db
from app.deps import get_current_user
from app.models.consumption import ConsumptionLog
from app.models.user import User
from app.schemas import FoodSuggestions
from app.services import consumption as engine, gemini, suggestions as suggestions_service
from app.services.nutrition import compute_targets

router = APIRouter(prefix="/api/consumption", tags=["consumption"])

_NUTRIENT_KEYS = ("calories", "protein_g", "carbs_g", "fat_g", "saturated_fat_g", "sugar_g", "fiber_g", "sodium_mg")


def _today() -> date:
    return engine.local_today()


def _logs_for(db: Session, user_id: int, day) -> list[ConsumptionLog]:
    stmt = select(ConsumptionLog).where(
        ConsumptionLog.user_id == user_id, ConsumptionLog.day == day
    ).order_by(ConsumptionLog.consumed_at)
    return list(db.scalars(stmt))


def _sum_consumed(logs: list[ConsumptionLog]) -> dict[str, float]:
    totals = {k: 0.0 for k in _NUTRIENT_KEYS}
    for log in logs:
        for k in _NUTRIENT_KEYS:
            totals[k] += getattr(log, k)
    return totals


def _entry(log: ConsumptionLog) -> ConsumptionEntry:
    return ConsumptionEntry(
        id=log.id,
        product_name=log.product_name,
        servings=round(log.servings, 2),
        calories=round(log.calories, 1),
        consumed_at=log.consumed_at.isoformat() if log.consumed_at else "",
    )


def _progress(db: Session, user: User) -> DailyProgress:
    targets = compute_targets(user.profile)
    logs = _logs_for(db, user.id, _today())
    consumed = _sum_consumed(logs)
    return engine.daily_progress(targets, consumed, [_entry(x) for x in logs])


@router.post("/preview", response_model=ConsumptionRecommendation)
def preview(payload: ConsumeInput, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    targets = compute_targets(current.profile)
    consumed = _sum_consumed(_logs_for(db, current.id, _today()))
    return engine.recommend(
        targets, consumed, payload.nutrition, payload.servings, payload.product_name, payload.product_verdict
    )


@router.post("/log", response_model=DailyProgress)
def log(payload: ConsumeInput, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    totals = engine.nutrition_totals(payload.nutrition, payload.servings)
    entry = ConsumptionLog(
        user_id=current.id,
        day=_today(),
        product_name=payload.product_name,
        servings=payload.servings,
        **{k: totals[k] for k in _NUTRIENT_KEYS},
    )
    db.add(entry)
    db.commit()
    return _progress(db, current)


@router.get("/today", response_model=DailyProgress)
def today(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _progress(db, current)


@router.delete("/{entry_id}", response_model=DailyProgress)
def delete_entry(entry_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.get(ConsumptionLog, entry_id)
    if entry is None or entry.user_id != current.id:
        raise HTTPException(status_code=404, detail="Entry not found.")
    db.delete(entry)
    db.commit()
    return _progress(db, current)


@router.get("/history", response_model=HistoryResponse)
def history(days: int = Query(7, ge=1, le=31), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    targets = compute_targets(current.profile)
    tvals = engine.target_values(targets)
    end = _today()
    start = end - timedelta(days=days - 1)

    stmt = select(ConsumptionLog).where(
        ConsumptionLog.user_id == current.id, ConsumptionLog.day >= start
    )
    by_day: dict = {}
    for log in db.scalars(stmt):
        by_day.setdefault(log.day, []).append(log)

    summaries = []
    for i in range(days):
        d = start + timedelta(days=i)
        logs = by_day.get(d, [])
        consumed = _sum_consumed(logs)
        summaries.append(
            DaySummary(
                date=d.isoformat(),
                achievement_pct=engine.achievement_pct(tvals, consumed),
                calories_consumed=round(consumed["calories"], 1),
                calories_target=targets.calories,
                entries=len(logs),
            )
        )
    return HistoryResponse(days=summaries)


@router.get("/weekly", response_model=WeeklyAverages)
def weekly(
    days: int = Query(7, ge=1, le=31),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WeeklyAverages:
    """Average daily intake + achievement over the last N days (unlogged days count as 0)."""
    targets = compute_targets(current.profile)
    end = _today()
    start = end - timedelta(days=days - 1)

    stmt = select(ConsumptionLog).where(
        ConsumptionLog.user_id == current.id,
        ConsumptionLog.day >= start,
        ConsumptionLog.day <= end,
    )
    by_day: dict = {}
    for log in db.scalars(stmt):
        by_day.setdefault(log.day, []).append(log)

    daily = [_sum_consumed(by_day.get(start + timedelta(days=i), [])) for i in range(days)]
    days_logged = sum(1 for i in range(days) if by_day.get(start + timedelta(days=i)))
    return engine.weekly_averages(targets, daily, days_logged)


@router.get("/suggestions", response_model=FoodSuggestions)
def suggestions(
    country: str | None = Query(None, description="Optional country for locally available foods"),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FoodSuggestions:
    """AI foods to fill what's LEFT of today's targets. Gaps are computed deterministically here;
    the model only picks foods (it never restates the numbers)."""
    logs = _logs_for(db, current.id, _today())
    targets = compute_targets(current.profile)
    consumed = _sum_consumed(logs)
    progress = engine.daily_progress(targets, consumed, [_entry(x) for x in logs])
    recent = [log.product_name for log in logs]
    goal = current.profile.goal.value if current.profile and current.profile.goal else None
    try:
        return suggestions_service.suggest(progress, country=country, goal=goal, recent_foods=recent)
    except gemini.AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

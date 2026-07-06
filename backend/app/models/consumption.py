"""Consumption log ORM model — one row per item a user records eating.

Stores the nutrient TOTALS actually consumed (servings already applied) as a numeric snapshot,
so historical entries stay correct even if the user later changes their profile/targets. `day`
is denormalized for cheap per-day grouping.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ConsumptionLog(Base):
    __tablename__ = "consumption_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    servings: Mapped[float] = mapped_column(Float, default=1.0)

    # Nutrient totals actually consumed (per-serving value × servings).
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    saturated_fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    sugar_g: Mapped[float] = mapped_column(Float, default=0.0)
    fiber_g: Mapped[float] = mapped_column(Float, default=0.0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0.0)

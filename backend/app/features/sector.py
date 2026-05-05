"""Sector/category features for ETF rotation strategy.

Computes sector-level momentum, relative strength, and exposure metrics.
"""
import numpy as np
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import DailyBar, Instrument


def compute_sector_momentum(
    db: Session,
    category: str,
    symbol_prices: dict[str, list[float]],
    window: int = 63,
) -> float:
    """Compute average momentum across all ETFs in a sector/category."""
    returns = []
    for symbol, prices in symbol_prices.items():
        if len(prices) > window:
            ret = (prices[-1] - prices[-window - 1]) / prices[-window - 1]
            returns.append(ret)
    return float(np.mean(returns)) if returns else 0.0


def compute_sector_relative_strength(
    sector_momentums: dict[str, float],
) -> dict[str, float]:
    """Normalize sector momentums to relative strength scores (-1 to 1)."""
    if not sector_momentums:
        return {}
    max_abs = max(abs(v) for v in sector_momentums.values()) or 1.0
    return {k: v / max_abs for k, v in sector_momentums.items()}


def get_instruments_by_category(db: Session) -> dict[str, list[Instrument]]:
    """Group instruments by category."""
    instruments = list(db.execute(select(Instrument)).scalars().all())
    groups: dict[str, list[Instrument]] = {}
    for inst in instruments:
        cat = inst.category or "uncategorized"
        groups.setdefault(cat, []).append(inst)
    return groups


def get_category_exposure(
    positions: dict[int, float],
    instruments: list[Instrument],
    prices: dict[int, float],
) -> dict[str, float]:
    """Compute current portfolio exposure by category."""
    total_value = sum(shares * prices.get(iid, 0) for iid, shares in positions.items())
    if total_value <= 0:
        return {}

    exposure: dict[str, float] = {}
    inst_map = {i.id: i for i in instruments}
    for iid, shares in positions.items():
        inst = inst_map.get(iid)
        if inst and iid in prices:
            cat = inst.category or "uncategorized"
            value = shares * prices[iid]
            exposure[cat] = exposure.get(cat, 0.0) + value / total_value

    return exposure

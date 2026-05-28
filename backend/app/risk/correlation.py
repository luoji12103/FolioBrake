"""Correlation matrix computation for ETF universe.

Flags diversification breakdown when correlations spike.
"""
import logging
from datetime import date

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import DailyBar, Instrument

logger = logging.getLogger(__name__)

CORRELATION_WARN_THRESHOLD = 0.80  # Flag pairs above this


class CorrelationMonitor:
    """Computes pairwise correlations among universe ETFs."""

    def __init__(self, db: Session):
        self.db = db

    def compute_matrix(
        self,
        instrument_ids: list[int],
        as_of_date: date,
        lookback: int = 60,
    ) -> dict:
        """Return correlation matrix and flagged pairs."""
        if len(instrument_ids) < 2:
            return {"matrix": [], "warnings": [], "note": "Need at least 2 instruments"}

        # Collect return series for each instrument
        return_series = {}
        symbols = {}

        for iid in instrument_ids:
            bars = self.db.execute(
                select(DailyBar).where(
                    DailyBar.instrument_id == iid,
                    DailyBar.trade_date <= as_of_date,
                ).order_by(DailyBar.trade_date.desc()).limit(lookback + 1)
            ).scalars().all()

            if len(bars) >= 2:
                prices = [b.close for b in reversed(bars)]
                prices_arr = np.array(prices[:-1])
                returns = list(np.where(prices_arr != 0, np.diff(prices) / prices_arr, 0.0))
                inst = self.db.execute(
                    select(Instrument).where(Instrument.id == iid)
                ).scalar_one_or_none()
                return_series[iid] = returns
                symbols[iid] = inst.symbol if inst else str(iid)

        if len(return_series) < 2:
            return {"matrix": [], "warnings": [], "note": "Insufficient price data"}

        # Compute pairwise correlations
        ids = list(return_series.keys())
        matrix = []
        warnings = []

        for i, id_a in enumerate(ids):
            for id_b in ids[i + 1:]:
                min_len = min(len(return_series[id_a]), len(return_series[id_b]))
                corr = float(np.corrcoef(return_series[id_a][-min_len:], return_series[id_b][-min_len:])[0, 1])
                pair = {
                    "a": symbols.get(id_a, str(id_a)),
                    "b": symbols.get(id_b, str(id_b)),
                    "correlation": round(corr, 4),
                }
                matrix.append(pair)
                if abs(corr) > CORRELATION_WARN_THRESHOLD:
                    warnings.append(pair)

        return {
            "matrix": sorted(matrix, key=lambda x: abs(x["correlation"]), reverse=True),
            "warnings": warnings,
            "lookback_days": lookback,
        }

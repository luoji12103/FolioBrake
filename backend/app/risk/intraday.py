"""Intra-day risk monitoring.

Checks price moves, volume anomalies, and gap changes during trading hours.
Controlled by ENABLE_INTRADAY_MONITORING config flag.
"""
import logging
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import DailyBar, Instrument
from app.risk.models import RiskRuleResultRecord

logger = logging.getLogger(__name__)

PRICE_MOVE_THRESHOLD = 0.05  # 5% intraday move triggers alert
VOLUME_SPIKE_MULTIPLE = 3.0  # 3x average volume triggers alert


class IntradayMonitor:
    """Monitors intraday price and volume conditions for risk alerts."""

    def __init__(self, db: Session):
        self.db = db

    def check(self, instrument_id: int, current_price: float, current_volume: float) -> list[RiskRuleResultRecord]:
        """Run intraday checks for a single instrument and return triggered alerts."""
        results = []
        today = date.today()

        # Get previous close for gap check
        prev_bar = self.db.execute(
            select(DailyBar).where(
                DailyBar.instrument_id == instrument_id,
                DailyBar.trade_date < today,
            ).order_by(DailyBar.trade_date.desc()).limit(1)
        ).scalar_one_or_none()

        if prev_bar:
            gap_pct = (current_price - prev_bar.close) / prev_bar.close
            if abs(gap_pct) > PRICE_MOVE_THRESHOLD:
                severity = "WARNING" if abs(gap_pct) > 0.10 else "INFO"
                results.append(RiskRuleResultRecord(
                    date=today, rule_name=f"intraday_price_move_{instrument_id}",
                    triggered=True, severity=severity,
                    detail={"gap_pct": gap_pct, "current": current_price, "prev_close": prev_bar.close},
                ))

        # Volume spike check
        avg_bars = self.db.execute(
            select(DailyBar).where(
                DailyBar.instrument_id == instrument_id,
                DailyBar.trade_date < today,
            ).order_by(DailyBar.trade_date.desc()).limit(20)
        ).scalars().all()

        if avg_bars:
            avg_vol = sum(b.volume for b in avg_bars) / len(avg_bars)
            if current_volume > avg_vol * VOLUME_SPIKE_MULTIPLE:
                results.append(RiskRuleResultRecord(
                    date=today, rule_name=f"intraday_volume_spike_{instrument_id}",
                    triggered=True, severity="WARNING",
                    detail={"current_volume": current_volume, "avg_volume": avg_vol},
                ))

        return results

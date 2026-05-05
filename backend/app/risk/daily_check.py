"""Daily market risk check — evaluates real market conditions against risk rules.

Wired into the strategy pipeline to scale positions based on risk state.
"""
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.risk.models import RiskProfile, RiskRuleResultRecord, RiskStateRecord
from app.risk.state_machine import RiskStateMachine
from app.data.models import DailyBar, Instrument

logger = logging.getLogger(__name__)

RISK_EXPOSURE_SCALE = {
    "NORMAL": 1.0,
    "CAUTION": 0.75,
    "DEFENSIVE": 0.50,
    "HALT": 0.0,
}


class MarketRiskEvaluator:
    """Evaluates daily market conditions and determines risk state."""

    def __init__(self, db: Session, profile: Optional[RiskProfile] = None):
        self.db = db
        self.profile = profile or self._default_profile()
        self.state_machine = RiskStateMachine(db)

    def _default_profile(self) -> RiskProfile:
        return RiskProfile(
            name="balanced",
            max_drawdown=-0.15,
            max_volatility=0.25,
            max_concentration=0.30,
        )

    def evaluate(self, as_of_date: date) -> RiskStateRecord:
        """Run risk rules against market data and return current state."""
        rule_results = []

        # Trend break: check market proxy (510050) vs SMA
        proxy = self._get_instrument("510050")
        if proxy:
            bars = self._get_bars(proxy.id, as_of_date, 200)
            if len(bars) >= 200:
                prices = [b.close for b in bars]
                sma_60 = sum(prices[-60:]) / 60
                current = prices[-1]
                momentum_20 = (prices[-1] - prices[-21]) / prices[-21] if len(prices) >= 21 else 0
                triggered = current < sma_60 and momentum_20 < 0
                rule_results.append(RiskRuleResultRecord(
                    date=as_of_date, rule_name="trend_break",
                    triggered=triggered,
                    severity="WARNING" if triggered else "INFO",
                    detail={"proxy_close": current, "sma_60": sma_60, "momentum": momentum_20},
                ))

        # Volatility spike: check 20-day realized vol
        if proxy:
            bars = self._get_bars(proxy.id, as_of_date, 120)
            if len(bars) >= 120:
                import numpy as np
                prices = [b.close for b in bars]
                daily_rets = np.diff(prices[-20:]) / prices[-21:-1]
                vol_20 = float(np.std(daily_rets) * np.sqrt(252))

                rolling_vols = []
                for i in range(100):
                    w = prices[-(20 + i):-i] if i > 0 else prices[-20:]
                    if len(w) < 21:
                        break
                    wr = np.diff(w) / w[:-1]
                    rolling_vols.append(float(np.std(wr) * np.sqrt(252)))
                pct = sum(1 for v in rolling_vols if v <= vol_20) / len(rolling_vols) if rolling_vols else 0.5

                triggered = pct > 0.90 or vol_20 > self.profile.max_volatility
                severity = "CRITICAL" if vol_20 > self.profile.max_volatility * 1.5 else ("WARNING" if triggered else "INFO")
                rule_results.append(RiskRuleResultRecord(
                    date=as_of_date, rule_name="volatility_spike",
                    triggered=triggered, severity=severity,
                    detail={"realized_vol": vol_20, "vol_percentile": pct},
                ))

        # Store rule results and evaluate state
        for r in rule_results:
            self.db.add(r)
        self.db.flush()

        return self.state_machine.evaluate(rule_results)

    def _get_instrument(self, symbol: str) -> Optional[Instrument]:
        return self.db.execute(
            select(Instrument).where(Instrument.symbol == symbol)
        ).scalar_one_or_none()

    def _get_bars(self, instrument_id: int, as_of_date: date, lookback: int) -> list:
        return list(self.db.execute(
            select(DailyBar).where(
                DailyBar.instrument_id == instrument_id,
                DailyBar.trade_date <= as_of_date,
            ).order_by(DailyBar.trade_date.desc()).limit(lookback)
        ).scalars().all())


def get_risk_scale(db: Session, as_of_date: date) -> float:
    """Convenience: evaluate risk and return exposure scale."""
    evaluator = MarketRiskEvaluator(db)
    state = evaluator.evaluate(as_of_date)
    return RISK_EXPOSURE_SCALE.get(state.state, 1.0)

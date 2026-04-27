from datetime import date

from app.risk.models import RiskProfile, RiskRuleResultRecord


class TrendBreakRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, market_index_close: float, market_sma_60: float,
              market_momentum: float, dt: date) -> RiskRuleResultRecord:
        below_ma = market_index_close < market_sma_60
        neg_momentum = market_momentum < 0
        triggered = below_ma and neg_momentum
        severity = "WARNING" if triggered else "INFO"
        return RiskRuleResultRecord(
            date=dt, rule_name="trend_break", triggered=triggered,
            severity=severity,
            detail={"market_close": market_index_close, "sma_60": market_sma_60,
                    "market_momentum": market_momentum, "below_ma": below_ma},
        )


class VolatilitySpikeRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, realized_vol: float, vol_percentile: float, dt: date) -> RiskRuleResultRecord:
        triggered = vol_percentile > 0.90 or realized_vol > self.profile.max_volatility
        severity = (
            "CRITICAL" if realized_vol > self.profile.max_volatility * 1.5
            else ("WARNING" if triggered else "INFO")
        )
        return RiskRuleResultRecord(
            date=dt, rule_name="volatility_spike", triggered=triggered,
            severity=severity,
            detail={"realized_vol": realized_vol, "vol_percentile": vol_percentile,
                    "threshold": self.profile.max_volatility},
        )


class DrawdownRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, portfolio_drawdown: float, dt: date) -> RiskRuleResultRecord:
        triggered = abs(portfolio_drawdown) > abs(self.profile.max_drawdown)
        severity = (
            "CRITICAL" if abs(portfolio_drawdown) > abs(self.profile.max_drawdown) * 1.5
            else ("WARNING" if triggered else "INFO")
        )
        return RiskRuleResultRecord(
            date=dt, rule_name="portfolio_drawdown", triggered=triggered,
            severity=severity,
            detail={"drawdown": portfolio_drawdown, "threshold": self.profile.max_drawdown},
        )


class LiquidityDegradationRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, etf_symbol: str, volume_ratio: float, dt: date) -> RiskRuleResultRecord:
        triggered = volume_ratio < 0.3
        return RiskRuleResultRecord(
            date=dt, rule_name=f"liquidity_degradation_{etf_symbol}",
            triggered=triggered, severity="WARNING" if triggered else "INFO",
            detail={"symbol": etf_symbol, "volume_ratio": volume_ratio},
        )


class CostCoverageRule:
    def __init__(self, risk_profile: RiskProfile):
        self.profile = risk_profile

    def check(self, estimated_cost_pct: float, expected_return_pct: float, dt: date) -> RiskRuleResultRecord:
        triggered = estimated_cost_pct > expected_return_pct * 0.5
        return RiskRuleResultRecord(
            date=dt, rule_name="cost_coverage", triggered=triggered,
            severity="WARNING" if triggered else "INFO",
            detail={"estimated_cost_pct": estimated_cost_pct, "expected_return_pct": expected_return_pct},
        )

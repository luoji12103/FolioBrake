from datetime import date
from sqlalchemy.orm import Session

from app.risk.state_machine import RiskStateMachine
from app.risk.rules import TrendBreakRule, VolatilitySpikeRule, DrawdownRule
from app.risk.models import RiskProfile, RiskOverlayDecisionRecord

DECISION_MAP = {"NORMAL": "ALLOW", "CAUTION": "REDUCE", "DEFENSIVE": "REDUCE", "HALT": "BLOCK"}


class RiskOverlay:
    def __init__(self, db: Session, risk_profile: RiskProfile):
        self.db = db
        self.profile = risk_profile
        self.state_machine = RiskStateMachine(db)
        self.rules = [
            TrendBreakRule(risk_profile),
            VolatilitySpikeRule(risk_profile),
            DrawdownRule(risk_profile),
        ]

    def apply(self, market_data: dict, portfolio_drawdown: float,
              target_portfolio: list[dict], dt: date) -> RiskOverlayDecisionRecord:
        rule_results = [
            self.rules[0].check(
                market_data.get("index_close", 0),
                market_data.get("index_sma_60", 0),
                market_data.get("market_momentum", 0),
                dt,
            ),
            self.rules[1].check(
                market_data.get("realized_vol", 0),
                market_data.get("vol_percentile", 0),
                dt,
            ),
            self.rules[2].check(portfolio_drawdown, dt),
        ]
        for r in rule_results:
            self.db.add(r)
        self.db.flush()

        state_record = self.state_machine.evaluate(rule_results)
        action = DECISION_MAP[state_record.state]

        final_targets = [{**t} for t in target_portfolio]
        suppressed_trades = []
        reason = f"Risk state: {state_record.state}. {state_record.transition_reason}"

        if action == "REDUCE":
            scale = 0.5 if state_record.state == "DEFENSIVE" else 0.75
            for t in final_targets:
                t["target_weight"] = t.get("target_weight", 0) * scale
            reason += f". Scaled positions to {scale*100:.0f}%"
        elif action == "BLOCK":
            suppressed_trades = [
                {"symbol": t.get("symbol"), "original_weight": t.get("target_weight")}
                for t in final_targets if t.get("target_weight", 0) > 0
            ]
            for t in final_targets:
                t["target_weight"] = 0.0
            reason += ". All risk-increasing trades blocked."

        decision = RiskOverlayDecisionRecord(
            date=dt,
            original_targets={"positions": target_portfolio},
            final_targets={"positions": final_targets},
            suppressed_trades={"trades": suppressed_trades},
            reason=reason,
            decision=action,
        )
        self.db.add(decision)
        self.db.flush()
        return decision

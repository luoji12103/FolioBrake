from datetime import date
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.risk.models import RiskStateRecord, RiskRuleResultRecord

STATE_ORDER = {"NORMAL": 0, "CAUTION": 1, "DEFENSIVE": 2, "HALT": 3}
STATES_BY_INDEX = ["NORMAL", "CAUTION", "DEFENSIVE", "HALT"]


class RiskStateMachine:
    def __init__(self, db: Session):
        self.db = db

    def get_current_state(self) -> str:
        result = self.db.execute(
            select(RiskStateRecord).order_by(desc(RiskStateRecord.date)).limit(1)
        ).scalar_one_or_none()
        return result.state if result else "NORMAL"

    def evaluate(self, rule_results: list[RiskRuleResultRecord]) -> RiskStateRecord:
        current_state = self.get_current_state()
        critical_count = sum(1 for r in rule_results if r.severity == "CRITICAL" and r.triggered)
        warning_count = sum(1 for r in rule_results if r.severity == "WARNING" and r.triggered)

        if critical_count >= 2:
            target_state = "HALT"
        elif critical_count >= 1:
            target_state = "DEFENSIVE"
        elif warning_count >= 3:
            target_state = "CAUTION"
        elif warning_count >= 1:
            target_state = "CAUTION"
        else:
            target_state = "NORMAL"

        current_idx = STATE_ORDER[current_state]
        target_idx = STATE_ORDER[target_state]

        if current_idx < target_idx:
            new_idx = min(current_idx + 1, target_idx)
        elif current_idx > target_idx:
            new_idx = max(current_idx - 1, target_idx)
        else:
            new_idx = current_idx

        new_state = STATES_BY_INDEX[new_idx]
        reason = f"Transition from {current_state} to {new_state}: critical_rules={critical_count}, warning_rules={warning_count}"

        record = RiskStateRecord(date=date.today(), state=new_state, transition_reason=reason)
        self.db.add(record)
        self.db.flush()
        return record

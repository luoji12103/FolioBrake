"""Strategy registry — supports multiple named strategies with discovery and comparison."""
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.strategy.models import StrategyConfig
from app.strategy.rotation import RiskAwareETFRotationV1

DEFAULT_STRATEGIES = {
    "risk_aware_etf_rotation_v1": {
        "name": "Risk-Aware ETF Rotation v1",
        "version": "v1",
        "parameters": {"max_holdings": 5, "max_concentration": 0.30, "min_positions": 3, "max_turnover": 0.50},
    },
    "equal_weight": {
        "name": "Equal-Weight ETF",
        "version": "v1",
        "parameters": {"max_holdings": 5, "max_concentration": 0.30, "allocation": "equal_weight"},
    },
    "risk_parity": {
        "name": "Risk-Parity (Inverse Vol)",
        "version": "v1",
        "parameters": {"max_holdings": 5, "max_concentration": 0.30, "allocation": "risk_parity"},
    },
}


class StrategyRegistry:
    """Manages available strategies and their configurations."""

    def __init__(self, db: Session):
        self.db = db

    def list_strategies(self) -> list[dict]:
        configs = list(self.db.execute(select(StrategyConfig)).scalars().all())
        if not configs:
            return [{"name": k, "version": v["version"], "parameters": v["parameters"]}
                    for k, v in DEFAULT_STRATEGIES.items()]
        return [{"name": c.name, "version": c.version, "parameters": c.parameters, "id": c.id}
                for c in configs]

    def get_or_create(self, name: str = "risk_aware_etf_rotation_v1") -> StrategyConfig:
        config = self.db.execute(
            select(StrategyConfig).where(StrategyConfig.name == name)
        ).scalar_one_or_none()

        if not config:
            defaults = DEFAULT_STRATEGIES.get(name, DEFAULT_STRATEGIES["risk_aware_etf_rotation_v1"])
            config = StrategyConfig(
                name=defaults["name"],
                version=defaults["version"],
                parameters=defaults["parameters"],
            )
            self.db.add(config)
            self.db.flush()

        return config

    def seed_defaults(self) -> int:
        """Ensure all default strategies exist. Returns count created."""
        count = 0
        for name in DEFAULT_STRATEGIES:
            existing = self.db.execute(
                select(StrategyConfig).where(StrategyConfig.name == name)
            ).scalar_one_or_none()
            if not existing:
                config = self.get_or_create(name)
                count += 1
        return count

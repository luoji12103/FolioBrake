import hashlib
import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.strategy.models import StrategyConfig, StrategyRun, Signal, TargetPortfolio, ExplanationLog
from app.features.registry import FeatureRegistry
from app.data.models import Instrument
from app.strategy.constraints import (
    apply_concentration_limit, apply_turnover_limit,
    apply_min_positions, apply_max_drawdown_check,
)

DEFAULT_FEATURE_WEIGHTS = {
    "trend": 0.25,
    "momentum": 0.30,
    "volatility": 0.15,
    "drawdown": 0.15,
    "liquidity": 0.15,
}


class RiskAwareETFRotationV1:
    def __init__(self, db: Session, config: StrategyConfig):
        self.db = db
        self.config = config
        self.feature_registry = FeatureRegistry(db)

    def _compute_config_hash(self) -> str:
        payload = json.dumps({
            "name": self.config.name,
            "version": self.config.version,
            "parameters": self.config.parameters,
            "feature_weights": DEFAULT_FEATURE_WEIGHTS,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def score_etf(self, instrument_id: int, as_of_date: date) -> dict:
        features = self.feature_registry.compute_all(instrument_id, as_of_date)
        if not features:
            return {"score": 0.0, "breakdown": {}}

        score = 0.0
        breakdown = {}
        for category, weight in DEFAULT_FEATURE_WEIGHTS.items():
            cat_features = {k: v for k, v in features.items() if k.startswith(category)}
            if cat_features:
                cat_score = sum(v for v in cat_features.values()) / len(cat_features)
            else:
                cat_score = 0.0
            score += weight * cat_score
            breakdown[category] = {
                "weight": weight,
                "sub_score": round(cat_score, 6),
                "features_used": list(cat_features.keys()),
            }
        return {"score": round(score, 6), "breakdown": breakdown}

    def build_portfolio(self, scores: list[dict], constraints: dict,
                        prev_weights: dict | None = None) -> list[dict]:
        ranked = sorted(scores, key=lambda x: x["score"], reverse=True)
        n_select = constraints.get("max_holdings", 5)
        min_score = constraints.get("min_score_threshold", -999)
        selected = [s for s in ranked[:n_select] if s["score"] >= min_score]

        if not selected:
            return []

        total_abs = sum(abs(s["score"]) for s in selected) or 1.0
        weights = [abs(s["score"]) / total_abs for s in selected]

        portfolio = []
        for s, w in zip(selected, weights):
            portfolio.append({
                "instrument_id": s["instrument_id"],
                "symbol": s.get("symbol", ""),
                "score": s["score"],
                "target_weight": round(w, 4),
                "breakdown": s.get("breakdown", {}),
            })

        portfolio = apply_concentration_limit(portfolio, constraints.get("max_concentration", 0.30))
        portfolio = apply_min_positions(portfolio, constraints.get("min_positions", 3))

        if prev_weights:
            portfolio = apply_turnover_limit(portfolio, prev_weights, constraints.get("max_turnover", 0.50))

        return portfolio

    def generate_signals(self, universe: list[Instrument], as_of_date: date) -> dict:
        scores = []
        for inst in universe:
            s = self.score_etf(inst.id, as_of_date)
            scores.append({"instrument_id": inst.id, "symbol": inst.symbol, **s})

        params = self.config.parameters or {}
        portfolio = self.build_portfolio(scores, params)

        config_hash = self._compute_config_hash()
        srun = StrategyRun(
            config_id=self.config.id,
            run_date=as_of_date,
            status="completed",
            config_hash=config_hash,
        )
        self.db.add(srun)
        self.db.flush()

        ranked = sorted(scores, key=lambda x: x["score"], reverse=True)
        for rank, s in enumerate(ranked, 1):
            signal = Signal(
                run_id=srun.id,
                instrument_id=s["instrument_id"],
                score=s["score"],
                rank=rank,
                reason={"breakdown": s.get("breakdown", {})},
            )
            self.db.add(signal)

        portfolio_ids = {p["instrument_id"] for p in portfolio}
        for inst in universe:
            action = "BUY" if inst.id in portfolio_ids else "SELL"
            instrument_score = next((s for s in scores if s["instrument_id"] == inst.id), None)
            sc = instrument_score or {"score": 0.0, "breakdown": {}}
            top_feature = ""
            if sc.get("breakdown"):
                top_cat = max(sc["breakdown"].items(),
                              key=lambda x: x[1]["weight"] * abs(x[1]["sub_score"]))
                top_feature = f"top driver={top_cat[0]} ({top_cat[1]['sub_score']:.3f})"

            log = ExplanationLog(
                run_id=srun.id,
                instrument_id=inst.id,
                action=action,
                reason=f"{inst.symbol}: action={action}, score={sc['score']:.3f}, {top_feature}",
                score_breakdown=sc.get("breakdown", {}),
            )
            self.db.add(log)

        for p in portfolio:
            tp = TargetPortfolio(
                run_id=srun.id,
                instrument_id=p["instrument_id"],
                target_weight=p["target_weight"],
                score=p["score"],
                constraint_info={"constraints": params},
            )
            self.db.add(tp)

        self.db.flush()
        return {
            "run_id": srun.id,
            "portfolio": portfolio,
        }

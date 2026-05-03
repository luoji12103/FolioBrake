from datetime import date, datetime, timedelta
import hashlib
import json

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtest.models import (
    BacktestConfig, BacktestRun, PortfolioSnapshot, SimulatedTrade, PerformanceMetric,
)
from app.strategy.models import StrategyConfig, StrategyRun
from app.strategy.rotation import RiskAwareETFRotationV1
from app.data.models import Instrument, DailyBar
from app.backtest.metrics import compute_sharpe, compute_max_drawdown, compute_cagr, compute_win_rate, compute_volatility

COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.001
MIN_CASH_BUFFER = 100.0  # Minimum cash to continue trading; below this, halt if no positions


def _weekly_dates(start: date, end: date) -> list[date]:
    """Generate weekly rebalance dates (Fridays)."""
    result = []
    current = start
    while current <= end:
        if current.weekday() == 4:  # Friday
            result.append(current)
        current += timedelta(days=1)
    return result


class BacktestEngine:
    def __init__(self, db: Session):
        self.db = db

    def run(self, config: BacktestConfig) -> BacktestRun:
        config_hash = hashlib.sha256(
            json.dumps({
                "start_date": str(config.start_date),
                "end_date": str(config.end_date),
                "initial_capital": config.initial_capital,
                "cost_model": config.cost_model,
                "strategy_config_id": config.strategy_config_id,
            }, sort_keys=True).encode()
        ).hexdigest()

        run = BacktestRun(config_id=config.id, config_hash=config_hash)
        self.db.add(run)
        self.db.flush()

        strat_config = self.db.execute(
            select(StrategyConfig).where(StrategyConfig.id == config.strategy_config_id)
        ).scalar_one()
        strategy = RiskAwareETFRotationV1(self.db, strat_config)
        universe = list(self.db.execute(select(Instrument)).scalars().all())

        rebalance_dates = _weekly_dates(config.start_date, config.end_date)
        if not rebalance_dates:
            return run

        cash = config.initial_capital
        positions: dict[int, float] = {}  # instrument_id -> shares
        equity_curve = [config.initial_capital]
        trades = []
        halted = False
        halt_reason = ""

        for week_date in rebalance_dates:
            # Price lookup: use most recent trading day <= rebalance date
            prices = {}
            for inst in universe:
                bar = self.db.execute(
                    select(DailyBar).where(
                        DailyBar.instrument_id == inst.id,
                        DailyBar.trade_date <= week_date,
                    ).order_by(DailyBar.trade_date.desc()).limit(1)
                ).scalar_one_or_none()
                if bar:
                    prices[inst.id] = bar.close

            if not prices:
                continue

            # Bankruptcy guard: if cash depleted and no positions, halt
            if cash <= MIN_CASH_BUFFER and not positions:
                if not halted:
                    halted = True
                    halt_reason = f"Bankrupt at {week_date}: cash ${cash:.2f} below buffer ${MIN_CASH_BUFFER:.0f}"
                continue

            # Run strategy
            result = strategy.generate_signals(universe, week_date)
            portfolio = result.get("portfolio", [])

            # Compute current total portfolio value (cash + holdings at market)
            total_value = cash
            for inst_id, shares in list(positions.items()):
                if inst_id in prices:
                    total_value += shares * prices[inst_id]

            # Liquidate old positions
            for inst_id, shares in list(positions.items()):
                if inst_id in prices:
                    cash += shares * prices[inst_id]
            positions.clear()

            # Buy new positions (with cost guard)
            target_weights = {p["instrument_id"]: p["target_weight"] for p in portfolio if p["target_weight"] > 0}
            for inst_id, target_w in target_weights.items():
                if inst_id not in prices:
                    continue
                target_value = total_value * target_w
                cost_price = prices[inst_id] * (1 + SLIPPAGE_RATE)
                shares = target_value / cost_price if cost_price > 0 else 0
                if shares <= 0:
                    continue
                cost = shares * cost_price
                commission = cost * COMMISSION_RATE
                if cash >= cost + commission:
                    positions[inst_id] = shares
                    cash -= cost + commission

            # Record snapshot
            new_value = cash
            for inst_id, shares in positions.items():
                if inst_id in prices:
                    new_value += shares * prices[inst_id]
            equity_curve.append(new_value)

            positions_json = [
                {"instrument_id": iid, "shares": sh,
                 "price": prices.get(iid, 0), "value": sh * prices.get(iid, 0)}
                for iid, sh in positions.items() if iid in prices
            ]
            daily_ret = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2] if len(equity_curve) >= 2 else 0.0
            snap = PortfolioSnapshot(
                run_id=run.id, date=week_date,
                total_value=new_value, cash=cash,
                positions={"positions": positions_json},
                daily_return=daily_ret,
            )
            self.db.add(snap)

            # Record trades
            for inst_id, shares in positions.items():
                if inst_id in prices:
                    p = prices[inst_id]
                    executed = p * (1 + SLIPPAGE_RATE)
                    comm = shares * executed * COMMISSION_RATE
                    trade = SimulatedTrade(
                        run_id=run.id, date=week_date,
                        instrument_id=inst_id,
                        side="BUY", quantity=shares,
                        price=p, executed_price=executed,
                        slippage=executed - p, commission=comm,
                        net_amount=shares * executed + comm,
                    )
                    self.db.add(trade)
                    trades.append({"pnl": 0.0})

        # Compute metrics
        returns = list(np.diff(equity_curve) / equity_curve[:-1]) if len(equity_curve) > 1 else []
        days = (config.end_date - config.start_date).days
        metrics = [
            ("total_return", (equity_curve[-1] - equity_curve[0]) / equity_curve[0] if equity_curve else 0.0),
            ("cagr", compute_cagr(equity_curve, days)),
            ("sharpe_ratio", compute_sharpe(returns)),
            ("max_drawdown", compute_max_drawdown(equity_curve)),
            ("volatility", compute_volatility(returns)),
            ("win_rate", compute_win_rate(trades)),
        ]
        if halted:
            metrics.append(("halted", 1.0))

        for name, val in metrics:
            self.db.add(PerformanceMetric(run_id=run.id, metric_name=name, value=val))

        run.status = "halted" if halted else "completed"
        run.completed_at = datetime.utcnow()
        self.db.flush()
        return run

"""Benchmark comparison integration for backtest results.

Syncs benchmark ETF data and computes relative performance metrics.
"""
from datetime import date
from typing import Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import DailyBar, Instrument
from app.backtest.metrics import compute_sharpe, compute_cagr, compute_max_drawdown


class BenchmarkComparison:
    """Computes strategy vs. benchmark relative performance."""

    def __init__(self, db: Session):
        self.db = db

    def sync_benchmark(self, benchmark_symbol: str = "510300") -> Optional[dict]:
        """Ensure benchmark data exists for comparison. Returns benchmark equity curve."""
        inst = self.db.execute(
            select(Instrument).where(Instrument.symbol == benchmark_symbol)
        ).scalar_one_or_none()

        if not inst:
            return None

        bars = list(self.db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == inst.id)
            .order_by(DailyBar.trade_date)
        ).scalars().all())

        if not bars:
            return None

        # Build buy-and-hold equity curve
        initial_price = bars[0].close
        return [{
            "date": str(b.trade_date),
            "total_value": b.close / initial_price * 100000,  # normalized to 100K
        } for b in bars]

    def compare(
        self,
        strategy_equity: list[dict],
        benchmark_equity: list[dict],
    ) -> dict:
        """Compute relative performance metrics."""
        # Align by date
        bench_map = {b["date"]: b["total_value"] for b in benchmark_equity}

        aligned_strat = []
        aligned_bench = []
        for s in strategy_equity:
            if s["date"] in bench_map:
                aligned_strat.append(s["total_value"])
                aligned_bench.append(bench_map[s["date"]])

        if len(aligned_strat) < 2:
            return {"note": "Insufficient aligned data for comparison"}

        strat_returns = list(np.diff(aligned_strat) / aligned_strat[:-1])
        bench_returns = list(np.diff(aligned_bench) / aligned_bench[:-1])

        excess_returns = [s - b for s, b in zip(strat_returns, bench_returns)]
        days = len(strat_returns)

        # Alpha: intercept of strategy returns vs benchmark returns
        if len(strat_returns) >= 2:
            cov = np.cov(strat_returns, bench_returns)
            bench_var = np.var(bench_returns)
            beta = cov[0][1] / bench_var if bench_var > 0 else 1.0
            alpha = (np.mean(strat_returns) - beta * np.mean(bench_returns)) * 252
        else:
            beta = 1.0
            alpha = 0.0

        # Information ratio
        tracking_error = float(np.std(excess_returns) * np.sqrt(252)) if excess_returns else 0.0
        info_ratio = float(np.mean(excess_returns) / (np.std(excess_returns) or 1e-10) * np.sqrt(252))

        return {
            "strategy_cagr": compute_cagr(aligned_strat, days),
            "benchmark_cagr": compute_cagr(aligned_bench, days),
            "strategy_sharpe": compute_sharpe(strat_returns),
            "benchmark_sharpe": compute_sharpe(bench_returns),
            "alpha": alpha,
            "beta": beta,
            "information_ratio": info_ratio,
            "tracking_error": tracking_error,
            "excess_return": (aligned_strat[-1] / aligned_strat[0]) - (aligned_bench[-1] / aligned_bench[0]) if aligned_bench[0] > 0 else 0.0,
        }

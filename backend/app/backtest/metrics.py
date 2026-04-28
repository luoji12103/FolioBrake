import numpy as np


def compute_returns(equity_curve: list[float]) -> list[float]:
    if len(equity_curve) < 2:
        return []
    return list(np.diff(equity_curve) / equity_curve[:-1])


def compute_sharpe(returns: list[float], risk_free: float = 0.02) -> float:
    if len(returns) < 2:
        return 0.0
    excess = np.mean(returns) - risk_free / 252
    std = np.std(returns) or 1e-10
    return float(excess / std * np.sqrt(252))


def compute_max_drawdown(equity: list[float]) -> float:
    if len(equity) < 2:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity[1:]:
        peak = max(peak, v)
        dd = (v - peak) / peak
        max_dd = min(max_dd, dd)
    return float(max_dd)


def compute_cagr(equity: list[float], days: int) -> float:
    if len(equity) < 2 or days <= 0:
        return 0.0
    total_return = (equity[-1] - equity[0]) / equity[0]
    years = days / 252
    if years <= 0:
        return 0.0
    # Guard against negative equity causing complex roots
    base = max(1 + total_return, 0.0001)
    return float(base ** (1 / years) - 1)


def compute_win_rate(trades: list[dict]) -> float:
    profitable = [t for t in trades if t.get("pnl", 0) > 0]
    return len(profitable) / len(trades) if trades else 0.0


def compute_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns) * np.sqrt(252))


def compare_to_benchmark(strategy_returns: list[float], benchmark_returns: list[float]) -> dict:
    min_len = min(len(strategy_returns), len(benchmark_returns))
    if min_len < 2:
        return {}
    strat_ret = strategy_returns[:min_len]
    bench_ret = benchmark_returns[:min_len]
    excess = [s - b for s, b in zip(strat_ret, bench_ret)]
    return {
        "strategy_cagr": compute_cagr(list(np.cumprod([1 + r for r in strat_ret]).tolist()), min_len),
        "benchmark_cagr": compute_cagr(list(np.cumprod([1 + r for r in bench_ret]).tolist()), min_len),
        "strategy_sharpe": compute_sharpe(strat_ret),
        "benchmark_sharpe": compute_sharpe(bench_ret),
        "information_ratio": (np.mean(excess) / (np.std(excess) or 1e-10)) * np.sqrt(252) if excess else 0.0,
        "tracking_error": float(np.std(excess) * np.sqrt(252)),
    }

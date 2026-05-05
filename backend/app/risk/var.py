"""Tail risk and VaR computation for portfolio and individual ETFs.

Computes Value-at-Risk (95%, 99%) and Conditional VaR from historical returns.
"""
import numpy as np


def compute_var(returns: list[float], confidence: float = 0.95) -> float:
    """Historical Value-at-Risk at given confidence level."""
    if len(returns) < 2:
        return 0.0
    sorted_rets = sorted(returns)
    idx = int(len(sorted_rets) * (1 - confidence))
    return -float(sorted_rets[max(0, min(idx, len(sorted_rets) - 1))])


def compute_cvar(returns: list[float], confidence: float = 0.95) -> float:
    """Conditional Value-at-Risk (expected shortfall beyond VaR)."""
    if len(returns) < 2:
        return 0.0
    var = compute_var(returns, confidence)
    tail = [r for r in returns if r <= -var]
    return -float(np.mean(tail)) if tail else var


def compute_tail_metrics(equity_curve: list[float]) -> dict:
    """Compute comprehensive tail risk metrics from equity curve."""
    if len(equity_curve) < 2:
        return {}

    returns = list(np.diff(equity_curve) / equity_curve[:-1])

    var_95 = compute_var(returns, 0.95)
    var_99 = compute_var(returns, 0.99)
    cvar_95 = compute_cvar(returns, 0.95)

    sorted_rets = sorted(returns)
    worst_day = sorted_rets[0]
    worst_week = min(sum(returns[i:i + 5]) for i in range(len(returns) - 4)) if len(returns) >= 5 else worst_day

    return {
        "var_95_daily": round(var_95, 6),
        "var_99_daily": round(var_99, 6),
        "cvar_95_daily": round(cvar_95, 6),
        "worst_day": round(worst_day, 6),
        "worst_week": round(worst_week, 6),
        "volatility_annualized": round(float(np.std(returns) * np.sqrt(252)), 4),
        "skewness": round(float(_skewness(returns)), 4),
        "kurtosis": round(float(_kurtosis(returns)), 4),
    }


def _skewness(data: list[float]) -> float:
    n = len(data)
    if n < 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return float(np.sum((data - mean) ** 3) / ((n - 1) * std ** 3))


def _kurtosis(data: list[float]) -> float:
    n = len(data)
    if n < 4:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return float(np.sum((data - mean) ** 4) / ((n - 1) * std ** 4) - 3)

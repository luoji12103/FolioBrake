from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from scipy import stats  # type: ignore[import-untyped]


def compute_var(returns: ArrayLike, confidence: float = 0.95) -> float:
    """Compute Value at Risk using percentile method.

    Args:
        returns: Array of historical returns.
        confidence: Confidence level (e.g. 0.95 for 95%).

    Returns:
        VaR value (negative number representing loss).
    """
    arr = np.asarray(returns, dtype=float)
    return float(np.percentile(arr, (1 - confidence) * 100))


def compute_cvar(returns: ArrayLike, confidence: float = 0.95) -> float:
    """Compute Conditional VaR (Expected Shortfall).

    Average of all returns that fall below the VaR threshold.

    Args:
        returns: Array of historical returns.
        confidence: Confidence level.

    Returns:
        CVaR value.
    """
    arr = np.asarray(returns, dtype=float)
    var = compute_var(arr, confidence)
    tail = arr[arr <= var]
    if len(tail) == 0:
        return var
    return float(np.mean(tail))


def compute_var_historical(returns: ArrayLike, confidence: float = 0.95) -> float:
    """Compute historical VaR by sorting returns.

    Args:
        returns: Array of historical returns.
        confidence: Confidence level.

    Returns:
        Historical VaR value.
    """
    sorted_returns = np.sort(np.asarray(returns, dtype=float))
    index = int((1 - confidence) * len(sorted_returns))
    index = max(0, min(index, len(sorted_returns) - 1))
    return float(sorted_returns[index])


def compute_var_parametric(returns: ArrayLike, confidence: float = 0.95) -> float:
    """Compute parametric VaR assuming normal distribution.

    Uses the formula: VaR = mu + z * sigma

    Args:
        returns: Array of historical returns.
        confidence: Confidence level.

    Returns:
        Parametric VaR value.
    """
    arr = np.asarray(returns, dtype=float)
    mu = float(np.mean(arr))
    sigma = float(np.std(arr))
    z = stats.norm.ppf(1 - confidence)
    return float(mu + z * sigma)


def compute_var_cornish_fisher(returns: ArrayLike, confidence: float = 0.95) -> float:
    """Compute VaR using Cornish-Fisher expansion for non-normal distributions.

    Adjusts the z-score for skewness and kurtosis.

    Args:
        returns: Array of historical returns.
        confidence: Confidence level.

    Returns:
        Cornish-Fisher adjusted VaR value.
    """
    arr = np.asarray(returns, dtype=float)
    mu = float(np.mean(arr))
    sigma = float(np.std(arr))
    s = float(stats.skew(arr))
    k = float(stats.kurtosis(arr))  # excess kurtosis

    z = stats.norm.ppf(1 - confidence)
    # Cornish-Fisher expansion
    z_cf = (
        z
        + (z**2 - 1) * s / 6
        + (z**3 - 3 * z) * k / 24
        - (2 * z**3 - 5 * z) * s**2 / 36
    )
    return float(mu + z_cf * sigma)


def compute_max_drawdown(returns: ArrayLike) -> float:
    """Compute maximum drawdown from a return series.

    Args:
        returns: Array of period returns.

    Returns:
        Maximum drawdown as a negative number.
    """
    arr = np.asarray(returns, dtype=float)
    cumulative = np.cumprod(1 + arr)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return float(np.min(drawdown))


def compute_risk_metrics_summary(returns: ArrayLike, confidence: float = 0.95) -> dict:
    """Compute a comprehensive set of risk metrics.

    Args:
        returns: Array of historical returns.
        confidence: Confidence level for VaR/CVaR.

    Returns:
        Dictionary of risk metrics.
    """
    arr = np.asarray(returns, dtype=float)

    return {
        "var": compute_var(arr, confidence),
        "cvar": compute_cvar(arr, confidence),
        "var_historical": compute_var_historical(arr, confidence),
        "var_parametric": compute_var_parametric(arr, confidence),
        "var_cornish_fisher": compute_var_cornish_fisher(arr, confidence),
        "max_drawdown": compute_max_drawdown(arr),
        "volatility": float(np.std(arr)),
        "annualized_volatility": float(np.std(arr) * np.sqrt(252)),
        "skewness": float(stats.skew(arr)),
        "kurtosis": float(stats.kurtosis(arr)),
        "mean_return": float(np.mean(arr)),
        "annualized_return": float(np.mean(arr) * 252),
        "sharpe_ratio": float(np.mean(arr) / np.std(arr) * np.sqrt(252)) if np.std(arr) > 0 else 0.0,
        "confidence": confidence,
        "num_observations": len(arr),
    }

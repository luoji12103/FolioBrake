from __future__ import annotations

import numpy as np
from typing import Sequence


def run_monte_carlo(
    returns: Sequence[float],
    num_simulations: int = 1000,
    num_days: int = 252,
    initial_value: float = 1.0,
) -> dict:
    """Run Monte Carlo simulation for future price paths.

    Uses geometric Brownian motion with drift and volatility estimated
    from historical returns.

    Args:
        returns: Historical daily returns.
        num_simulations: Number of simulation paths.
        num_days: Number of trading days to simulate.
        initial_value: Starting value (normalized to 1.0 by default).

    Returns:
        Dict with simulation results and statistics.
    """
    arr = np.asarray(returns, dtype=float)
    mu = float(np.mean(arr))
    sigma = float(np.std(arr))

    if sigma == 0:
        # Degenerate case: no volatility
        path = [float(initial_value * (1 + mu) ** d) for d in range(num_days + 1)]
        return {
            "simulations": [path],
            "mean_final": path[-1],
            "std_final": 0.0,
            "percentile_5": path[-1],
            "percentile_25": path[-1],
            "percentile_50": path[-1],
            "percentile_75": path[-1],
            "percentile_95": path[-1],
            "mean_daily_return": mu,
            "daily_volatility": sigma,
            "num_simulations": 1,
            "num_days": num_days,
        }

    # Generate all random returns at once for efficiency
    random_returns = np.random.normal(mu, sigma, (num_simulations, num_days))

    # Compute cumulative returns
    cumulative = initial_value * np.cumprod(1 + random_returns, axis=1)

    # Prepend initial value
    initial_col = np.full((num_simulations, 1), initial_value)
    paths = np.hstack([initial_col, cumulative])

    # Compute statistics
    final_values = paths[:, -1]

    return {
        "simulations": paths.tolist(),
        "mean_final": float(np.mean(final_values)),
        "std_final": float(np.std(final_values)),
        "percentile_5": float(np.percentile(final_values, 5)),
        "percentile_25": float(np.percentile(final_values, 25)),
        "percentile_50": float(np.percentile(final_values, 50)),
        "percentile_75": float(np.percentile(final_values, 75)),
        "percentile_95": float(np.percentile(final_values, 95)),
        "mean_daily_return": mu,
        "daily_volatility": sigma,
        "num_simulations": num_simulations,
        "num_days": num_days,
    }


def run_monte_carlo_var(
    returns: Sequence[float],
    portfolio_value: float,
    num_simulations: int = 10000,
    horizon_days: int = 10,
    confidence: float = 0.95,
) -> dict:
    """Run Monte Carlo simulation to compute VaR over a horizon.

    Args:
        returns: Historical daily returns.
        portfolio_value: Current portfolio value.
        num_simulations: Number of simulation paths.
        horizon_days: Investment horizon in trading days.
        confidence: Confidence level for VaR.

    Returns:
        Dict with VaR and simulation statistics.
    """
    arr = np.asarray(returns, dtype=float)
    mu = float(np.mean(arr))
    sigma = float(np.std(arr))

    # Simulate horizon returns
    random_returns = np.random.normal(mu, sigma, (num_simulations, horizon_days))
    cumulative_returns = np.prod(1 + random_returns, axis=1) - 1

    # Compute portfolio P&L
    pnl = portfolio_value * cumulative_returns

    var = float(np.percentile(pnl, (1 - confidence) * 100))
    cvar = float(np.mean(pnl[pnl <= var])) if np.any(pnl <= var) else var

    return {
        "portfolio_value": portfolio_value,
        "horizon_days": horizon_days,
        "confidence": confidence,
        "var": var,
        "cvar": cvar,
        "var_pct": var / portfolio_value if portfolio_value > 0 else 0.0,
        "cvar_pct": cvar / portfolio_value if portfolio_value > 0 else 0.0,
        "mean_pnl": float(np.mean(pnl)),
        "std_pnl": float(np.std(pnl)),
        "worst_case": float(np.min(pnl)),
        "best_case": float(np.max(pnl)),
        "prob_loss": float(np.mean(pnl < 0)),
        "num_simulations": num_simulations,
    }


def run_monte_carlo_portfolio(
    weights: list[float],
    returns_matrix: list[list[float]],
    num_simulations: int = 1000,
    num_days: int = 252,
    initial_value: float = 1.0,
) -> dict:
    """Run Monte Carlo simulation for a multi-asset portfolio.

    Uses correlated returns from historical data.

    Args:
        weights: Portfolio weights for each asset.
        returns_matrix: List of return series, one per asset.
        num_simulations: Number of simulation paths.
        num_days: Trading days to simulate.
        initial_value: Starting portfolio value.

    Returns:
        Dict with portfolio simulation results.
    """
    returns_arr = np.array(returns_matrix)  # shape: (n_assets, n_obs)
    weights_arr = np.array(weights)

    # Compute mean returns and covariance matrix
    mean_returns = np.mean(returns_arr, axis=1)
    cov_matrix = np.cov(returns_arr)

    # Cholesky decomposition for correlated random returns
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # Covariance matrix not positive definite; add small diagonal
        cov_matrix += np.eye(len(weights)) * 1e-8
        L = np.linalg.cholesky(cov_matrix)

    n_assets = len(weights)
    portfolio_paths = np.zeros((num_simulations, num_days + 1))
    portfolio_paths[:, 0] = initial_value

    for sim in range(num_simulations):
        z = np.random.standard_normal((n_assets, num_days))
        correlated_returns = mean_returns[:, None] + L @ z  # (n_assets, num_days)
        portfolio_daily_returns = weights_arr @ correlated_returns  # (num_days,)
        portfolio_paths[sim, 1:] = initial_value * np.cumprod(1 + portfolio_daily_returns)

    final_values = portfolio_paths[:, -1]

    return {
        "simulations": portfolio_paths.tolist(),
        "mean_final": float(np.mean(final_values)),
        "std_final": float(np.std(final_values)),
        "percentile_5": float(np.percentile(final_values, 5)),
        "percentile_95": float(np.percentile(final_values, 95)),
        "num_simulations": num_simulations,
        "num_days": num_days,
        "num_assets": n_assets,
    }

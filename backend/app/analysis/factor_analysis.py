from __future__ import annotations

import numpy as np
from scipy import stats  # type: ignore[import-untyped]
from typing import Sequence


def compute_pca(returns_matrix: list[list[float]], n_factors: int = 3) -> dict:
    """Perform Principal Component Analysis on asset returns.

    Args:
        returns_matrix: List of return series, one per asset.
        n_factors: Number of principal components to extract.

    Returns:
        Dict with eigenvalues, eigenvectors, and explained variance.
    """
    arr = np.array(returns_matrix)  # shape: (n_assets, n_obs)

    # Standardize returns
    means = np.mean(arr, axis=1, keepdims=True)
    stds = np.std(arr, axis=1, keepdims=True)
    stds[stds == 0] = 1.0  # Avoid division by zero
    standardized = (arr - means) / stds

    # Compute correlation matrix
    corr_matrix = np.corrcoef(standardized)

    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)

    # Sort by eigenvalue (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Limit to n_factors
    n_factors = min(n_factors, len(eigenvalues))
    eigenvalues = eigenvalues[:n_factors]
    eigenvectors = eigenvectors[:, :n_factors]

    # Explained variance
    total_var = np.sum(np.linalg.eigvalsh(corr_matrix))
    explained_variance = eigenvalues / total_var
    cumulative_variance = np.cumsum(explained_variance)

    # Factor loadings = eigenvectors * sqrt(eigenvalues)
    loadings = eigenvectors * np.sqrt(eigenvalues)

    return {
        "eigenvalues": eigenvalues.tolist(),
        "eigenvectors": eigenvectors.tolist(),
        "loadings": loadings.tolist(),
        "explained_variance_ratio": explained_variance.tolist(),
        "cumulative_variance_ratio": cumulative_variance.tolist(),
        "n_factors": n_factors,
        "n_assets": arr.shape[0],
    }


def compute_fundamental_factor_scores(
    factor_values: dict[str, list[float]],
    returns: list[float],
) -> dict:
    """Compute factor scores using cross-sectional regression.

    Args:
        factor_values: Dict mapping factor names to lists of values per asset.
        returns: List of returns per asset (cross-sectional).

    Returns:
        Dict with factor betas, t-stats, and R-squared.
    """
    factor_names = list(factor_values.keys())
    n_factors = len(factor_names)
    n_assets = len(returns)

    if n_assets < n_factors + 1:
        return {
            "error": "Insufficient assets for factor regression",
            "n_assets": n_assets,
            "n_factors": n_factors,
        }

    # Build design matrix
    X = np.column_stack([factor_values[f] for f in factor_names])
    y = np.array(returns)

    # Add intercept
    X_with_intercept = np.column_stack([np.ones(n_assets), X])

    # OLS regression
    try:
        beta, residuals, rank, sv = np.linalg.lstsq(X_with_intercept, y, rcond=None)
    except np.linalg.LinAlgError:
        return {"error": "Regression failed"}

    # Compute statistics
    y_hat = X_with_intercept @ beta
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Standard errors
    if n_assets > n_factors + 1:
        mse = ss_res / (n_assets - n_factors - 1)
        try:
            se = np.sqrt(np.diag(mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)))
        except np.linalg.LinAlgError:
            se = np.full(n_factors + 1, np.nan)
        t_stats = beta / se
    else:
        se = np.full(n_factors + 1, np.nan)
        t_stats = np.full(n_factors + 1, np.nan)

    return {
        "intercept": float(beta[0]),
        "factor_betas": {name: float(beta[i + 1]) for i, name in enumerate(factor_names)},
        "t_statistics": {name: float(t_stats[i + 1]) for i, name in enumerate(factor_names)},
        "intercept_t_stat": float(t_stats[0]),
        "r_squared": float(r_squared),
        "n_assets": n_assets,
        "n_factors": n_factors,
    }


def compute_rolling_factor_betas(
    returns_matrix: list[list[float]],
    market_returns: list[float],
    window: int = 60,
) -> dict:
    """Compute rolling beta relative to market for each asset.

    Args:
        returns_matrix: List of return series, one per asset.
        market_returns: Market index returns.
        window: Rolling window size in trading days.

    Returns:
        Dict with rolling beta series per asset.
    """
    n_assets = len(returns_matrix)
    n_obs = len(market_returns)
    market_arr = np.array(market_returns)

    rolling_betas = []
    for i in range(n_assets):
        asset_arr = np.array(returns_matrix[i])
        min_len = min(len(asset_arr), n_obs)
        asset_arr = asset_arr[:min_len]
        mkt = market_arr[:min_len]

        betas = []
        for t in range(window, min_len):
            y = asset_arr[t - window : t]
            x = mkt[t - window : t]

            # Simple OLS: y = alpha + beta * x
            x_with_intercept = np.column_stack([np.ones(window), x])
            try:
                coeff = np.linalg.lstsq(x_with_intercept, y, rcond=None)[0]
                betas.append(float(coeff[1]))
            except np.linalg.LinAlgError:
                betas.append(np.nan)

        rolling_betas.append(betas)

    return {
        "rolling_betas": rolling_betas,
        "window": window,
        "n_assets": n_assets,
    }


def compute_factor_correlation(
    factor_values: dict[str, list[float]],
) -> dict:
    """Compute correlation matrix between factors.

    Args:
        factor_values: Dict mapping factor names to value arrays.

    Returns:
        Dict with factor names and correlation matrix.
    """
    names = list(factor_values.keys())
    arr = np.array([factor_values[n] for n in names])

    corr = np.corrcoef(arr)

    return {
        "factor_names": names,
        "correlation_matrix": corr.tolist(),
    }

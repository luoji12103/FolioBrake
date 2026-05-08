from __future__ import annotations

import numpy as np
from typing import Sequence


def compute_bid_ask_spread(
    bid_prices: Sequence[float],
    ask_prices: Sequence[float],
) -> dict:
    """Compute bid-ask spread statistics.

    Args:
        bid_prices: Array of bid prices.
        ask_prices: Array of ask prices.

    Returns:
        Dict with spread statistics.
    """
    bid = np.asarray(bid_prices, dtype=float)
    ask = np.asarray(ask_prices, dtype=float)

    spread = ask - bid
    mid = (ask + bid) / 2
    relative_spread = spread / mid

    return {
        "mean_spread": float(np.mean(spread)),
        "median_spread": float(np.median(spread)),
        "std_spread": float(np.std(spread)),
        "mean_relative_spread": float(np.mean(relative_spread)),
        "median_relative_spread": float(np.median(relative_spread)),
        "max_spread": float(np.max(spread)),
        "min_spread": float(np.min(spread)),
        "num_observations": len(spread),
    }


def compute_market_impact(
    trade_sizes: Sequence[float],
    price_changes: Sequence[float],
) -> dict:
    """Estimate market impact model: price_change = a * sqrt(trade_size) + b.

    Uses square-root model common in market microstructure.

    Args:
        trade_sizes: Array of trade sizes (shares or value).
        price_changes: Array of observed price changes.

    Returns:
        Dict with impact model parameters and fit statistics.
    """
    sizes = np.asarray(trade_sizes, dtype=float)
    changes = np.asarray(price_changes, dtype=float)

    # Square-root model: Δp = a * √(size) + b
    sqrt_sizes = np.sqrt(sizes)
    X = np.column_stack([np.ones(len(sizes)), sqrt_sizes])

    try:
        coeffs = np.linalg.lstsq(X, changes, rcond=None)[0]
    except np.linalg.LinAlgError:
        return {"error": "Regression failed"}

    b, a = coeffs
    y_hat = X @ coeffs
    ss_res = np.sum((changes - y_hat) ** 2)
    ss_tot = np.sum((changes - np.mean(changes)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "impact_coefficient": float(a),
        "baseline_impact": float(b),
        "r_squared": float(r_squared),
        "model": "price_change = a * sqrt(trade_size) + b",
        "num_trades": len(sizes),
    }


def compute_order_imbalance(
    buy_volumes: Sequence[float],
    sell_volumes: Sequence[float],
) -> dict:
    """Compute order flow imbalance.

    Imbalance = (buy_vol - sell_vol) / (buy_vol + sell_vol)

    Args:
        buy_volumes: Array of buy volumes per period.
        sell_volumes: Array of sell volumes per period.

    Returns:
        Dict with imbalance statistics.
    """
    buy = np.asarray(buy_volumes, dtype=float)
    sell = np.asarray(sell_volumes, dtype=float)

    total = buy + sell
    # Avoid division by zero
    imbalance = np.where(total > 0, (buy - sell) / total, 0.0)

    return {
        "mean_imbalance": float(np.mean(imbalance)),
        "std_imbalance": float(np.std(imbalance)),
        "median_imbalance": float(np.median(imbalance)),
        "max_imbalance": float(np.max(imbalance)),
        "min_imbalance": float(np.min(imbalance)),
        "total_buy_volume": float(np.sum(buy)),
        "total_sell_volume": float(np.sum(sell)),
        "net_order_flow": float(np.sum(buy) - np.sum(sell)),
        "num_periods": len(imbalance),
    }


def compute_vwap_deviation(
    prices: Sequence[float],
    volumes: Sequence[float],
    vwap: float,
) -> dict:
    """Compute VWAP deviation metrics.

    Args:
        prices: Array of trade prices.
        volumes: Array of trade volumes.
        vwap: Volume-weighted average price.

    Returns:
        Dict with VWAP deviation statistics.
    """
    p = np.asarray(prices, dtype=float)
    v = np.asarray(volumes, dtype=float)

    deviations = (p - vwap) / vwap
    volume_weighted_dev = np.sum(deviations * v) / np.sum(v) if np.sum(v) > 0 else 0.0

    return {
        "vwap": float(vwap),
        "mean_deviation": float(np.mean(deviations)),
        "std_deviation": float(np.std(deviations)),
        "volume_weighted_deviation": float(volume_weighted_dev),
        "max_deviation": float(np.max(deviations)),
        "min_deviation": float(np.min(deviations)),
        "total_volume": float(np.sum(v)),
        "num_trades": len(p),
    }


def compute_realized_volatility(
    prices: Sequence[float],
    window: int = 20,
) -> dict:
    """Compute realized volatility using high-frequency-style approach.

    Args:
        prices: Array of prices (can be intraday or daily).
        window: Window for rolling computation.

    Returns:
        Dict with realized volatility series and statistics.
    """
    p = np.asarray(prices, dtype=float)
    log_returns = np.diff(np.log(p))

    # Squared returns for realized variance
    sq_returns = log_returns**2

    # Rolling realized volatility
    rv_series = []
    for i in range(window, len(sq_returns) + 1):
        rv = np.sqrt(np.sum(sq_returns[i - window : i]) * 252)
        rv_series.append(float(rv))

    return {
        "realized_volatility": rv_series,
        "mean_rv": float(np.mean(rv_series)) if rv_series else 0.0,
        "std_rv": float(np.std(rv_series)) if rv_series else 0.0,
        "current_rv": rv_series[-1] if rv_series else 0.0,
        "window": window,
        "num_observations": len(rv_series),
    }


def compute_amihud_illiquidity(
    returns: Sequence[float],
    volumes: Sequence[float],
) -> dict:
    """Compute Amihud illiquidity ratio.

    Illiquidity = |return| / dollar_volume

    Args:
        returns: Array of returns.
        volumes: Array of dollar (or yuan) trading volumes.

    Returns:
        Dict with illiquidity statistics.
    """
    r = np.asarray(returns, dtype=float)
    v = np.asarray(volumes, dtype=float)

    # Filter out zero volumes
    mask = v > 0
    r = r[mask]
    v = v[mask]

    if len(r) == 0:
        return {
            "amihud_ratio": 0.0,
            "mean_illiquidity": 0.0,
            "num_observations": 0,
        }

    illiquidity = np.abs(r) / v

    return {
        "amihud_ratio": float(np.mean(illiquidity)),
        "mean_illiquidity": float(np.mean(illiquidity)),
        "median_illiquidity": float(np.median(illiquidity)),
        "std_illiquidity": float(np.std(illiquidity)),
        "num_observations": int(np.sum(mask)),
    }

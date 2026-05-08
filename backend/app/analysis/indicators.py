from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Sequence


def compute_ma(prices: list[float], window: int) -> list[float | None]:
    result = pd.Series(prices).rolling(window=window).mean()
    return [None if pd.isna(v) else float(v) for v in result]


def compute_ema(prices: list[float], window: int) -> list[float | None]:
    result = pd.Series(prices).ewm(span=window, adjust=False).mean()
    return [None if pd.isna(v) else float(v) for v in result]


def compute_rsi(prices: Sequence[float], period: int = 14) -> list[float | None]:
    if len(prices) < period + 1:
        return [None for _ in prices]

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    rsi: list[float | None] = [None for _ in range(period)]
    if down == 0:
        rsi.append(100.0)
    else:
        rs = up / down
        rsi.append(100.0 - 100.0 / (1.0 + rs))

    for i in range(period, len(deltas)):
        delta = deltas[i]
        upval = delta if delta > 0 else 0.0
        downval = -delta if delta < 0 else 0.0

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        if down == 0:
            rsi.append(100.0)
        else:
            rs = up / down
            rsi.append(100.0 - 100.0 / (1.0 + rs))

    return rsi


def compute_macd(
    prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> dict[str, list[float]]:
    s = pd.Series(prices)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": macd_line.tolist(),
        "signal": signal_line.tolist(),
        "histogram": histogram.tolist(),
    }


def compute_bollinger_bands(
    prices: list[float], window: int = 20, num_std: float = 2.0
) -> dict[str, list[float | None]]:
    s = pd.Series(prices)
    middle = s.rolling(window=window).mean()
    std = s.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return {
        "upper": [None if pd.isna(v) else float(v) for v in upper],
        "middle": [None if pd.isna(v) else float(v) for v in middle],
        "lower": [None if pd.isna(v) else float(v) for v in lower],
    }


def compute_volatility_series(
    prices: list[float], window: int = 20
) -> list[float | None]:
    s = pd.Series(prices)
    returns = s.pct_change().dropna()
    rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)
    return [None] + [None if pd.isna(v) else float(v) for v in rolling_vol]


def compute_drawdown_series(prices: list[float]) -> dict[str, list]:
    if not prices:
        return {"drawdown": [], "peak": [], "trough": []}

    peak = prices[0]
    drawdowns = []
    peaks = []
    for p in prices:
        peak = max(peak, p)
        dd = (p - peak) / peak if peak != 0 else 0.0
        drawdowns.append(dd)
        peaks.append(peak)

    return {"drawdown": drawdowns, "peak": peaks}


def compute_correlation_matrix(
    price_series: dict[str, list[float]]
) -> dict[str, list]:
    symbols = list(price_series.keys())
    n = len(symbols)
    if n == 0:
        return {"symbols": [], "matrix": []}

    returns = {}
    min_len = float("inf")
    for sym in symbols:
        p = price_series[sym]
        if len(p) < 2:
            returns[sym] = []
            continue
        r = np.diff(p) / np.array(p[:-1])
        returns[sym] = r
        min_len = min(min_len, len(r))

    if min_len < 2 or min_len == float("inf"):
        return {"symbols": symbols, "matrix": [[0.0] * n for _ in range(n)]}

    min_len = int(min_len)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            ri = returns[symbols[i]][-min_len:]
            rj = returns[symbols[j]][-min_len:]
            if len(ri) > 1 and len(rj) > 1:
                corr = np.corrcoef(ri, rj)[0][1]
                matrix[i][j] = float(corr) if not np.isnan(corr) else 0.0
            else:
                matrix[i][j] = 0.0

    return {"symbols": symbols, "matrix": matrix.tolist()}


def compute_return_attribution(
    portfolio_returns: list[float],
    benchmark_returns: list[float],
    factor_names: list[str] | None = None,
) -> dict:
    p = np.array(portfolio_returns)
    b = np.array(benchmark_returns)
    min_len = min(len(p), len(b))
    if min_len < 2:
        return {
            "active_return": 0.0,
            "tracking_error": 0.0,
            "information_ratio": 0.0,
            "portfolio_cumulative": [],
            "benchmark_cumulative": [],
            "active_cumulative": [],
        }

    p = p[:min_len]
    b = b[:min_len]
    active = p - b

    active_return = float(np.mean(active) * 252)
    tracking_error = float(np.std(active) * np.sqrt(252))
    info_ratio = active_return / tracking_error if tracking_error > 0 else 0.0

    portfolio_cum = np.cumprod(1 + p).tolist()
    benchmark_cum = np.cumprod(1 + b).tolist()
    active_cum = np.cumprod(1 + active).tolist()

    return {
        "active_return": active_return,
        "tracking_error": tracking_error,
        "information_ratio": info_ratio,
        "portfolio_cumulative": portfolio_cum,
        "benchmark_cumulative": benchmark_cum,
        "active_cumulative": active_cum,
    }

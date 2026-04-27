import numpy as np
from datetime import date


def _sma(prices: list[float], window: int) -> float:
    if len(prices) < window:
        return 0.0
    return float(np.mean(prices[-window:]))


def _ema(prices: list[float], window: int) -> float:
    if len(prices) < window:
        return 0.0
    alpha = 2.0 / (window + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = alpha * p + (1 - alpha) * ema
    return ema


def compute_trend_features(prefix: str, prices: list[float], dates: list[date],
                           params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    for w in [20, 60, 120, 200]:
        if len(prices) >= w:
            sma_val = _sma(prices, w)
            results[f"{prefix}_sma_{w}"] = sma_val
            results[f"{prefix}_price_vs_sma_{w}"] = (
                (prices[-1] - sma_val) / sma_val if sma_val else 0.0
            )

    if len(prices) >= 61:
        prev_sma = _sma(prices[:-1], 60)
        curr_sma = _sma(prices, 60)
        results[f"{prefix}_sma_60_slope"] = (
            (curr_sma - prev_sma) / prev_sma if prev_sma else 0.0
        )

    if len(prices) >= 26:
        ema12 = _ema(prices, 12)
        ema26 = _ema(prices, 26)
        results[f"{prefix}_ema_crossover"] = 1.0 if ema12 > ema26 else -1.0

    return results

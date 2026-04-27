import numpy as np
from datetime import date


def compute_volatility_features(prefix: str, prices: list[float], dates: list[date],
                                 params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    for w in [20, 60]:
        if len(prices) > w:
            daily_rets = np.diff(prices[-w:]) / prices[-w:-1]
            vol = float(np.std(daily_rets) * np.sqrt(252))
            results[f"{prefix}_realized_vol_{w}d"] = vol

    if len(prices) >= 252:
        daily_rets_20 = np.diff(prices[-20:]) / prices[-21:-1]
        vol_20 = float(np.std(daily_rets_20) * np.sqrt(252))
        rolling_vols = []
        for i in range(252 - 20):
            start = -(252 - i)
            end = -(252 - i - 21)
            window_rets = np.diff(prices[start:end]) / prices[start - 1:end - 1]
            rolling_vols.append(float(np.std(window_rets) * np.sqrt(252)))
        if rolling_vols:
            pct_rank = sum(1 for v in rolling_vols if v <= vol_20) / len(rolling_vols)
            results[f"{prefix}_vol_percentile"] = pct_rank

    return results

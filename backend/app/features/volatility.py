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
        daily_rets_20 = np.diff(prices[-20:]) / prices[-20:-1]
        vol_20 = float(np.std(daily_rets_20) * np.sqrt(252))
        rolling_vols = []
        n_windows = len(prices) - 252
        for i in range(max(1, n_windows)):
            w_start = -(252 + i)
            w_end = -(i + 1) if i > 0 else None
            window = prices[w_start:w_end]
            if len(window) < 22:
                break
            window_rets = np.diff(window) / window[:-1]
            rolling_vols.append(float(np.std(window_rets) * np.sqrt(252)))
        if rolling_vols:
            pct_rank = sum(1 for v in rolling_vols if v <= vol_20) / len(rolling_vols)
            results[f"{prefix}_vol_percentile"] = pct_rank

    return results

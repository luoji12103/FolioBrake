import numpy as np
from datetime import date


def compute_liquidity_features(prefix: str, volumes: list[float], dates: list[date],
                                 params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    if len(volumes) < 5:
        return results

    for w in [20, 60]:
        if len(volumes) >= w:
            results[f"{prefix}_adv_{w}d"] = float(np.mean(volumes[-w:]))
            if w == 20 and len(volumes) >= 60:
                adv20 = float(np.mean(volumes[-20:]))
                adv60 = float(np.mean(volumes[-60:]))
                results[f"{prefix}_volume_trend"] = adv20 / adv60 if adv60 > 0 else 1.0

    zero_days = sum(1 for v in volumes[-20:] if v == 0)
    results[f"{prefix}_zero_vol_days_20d"] = float(zero_days)

    return results

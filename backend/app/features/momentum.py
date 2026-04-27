import numpy as np
from datetime import date


def compute_momentum_features(prefix: str, prices: list[float], dates: list[date],
                               params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    window_labels = {21: "1m", 63: "3m", 126: "6m", 252: "12m"}
    for window, label in window_labels.items():
        if len(prices) > window:
            ret = (prices[-1] - prices[-window - 1]) / prices[-window - 1]
            results[f"{prefix}_return_{label}"] = ret

    if len(prices) >= 127:
        ret_6m = (prices[-1] - prices[-127]) / prices[-127]
        daily_rets = np.diff(prices[-127:]) / prices[-127:-1]
        vol = float(np.std(daily_rets) * np.sqrt(252))
        results[f"{prefix}_risk_adj_momentum"] = ret_6m / vol if vol > 0 else 0.0

    return results

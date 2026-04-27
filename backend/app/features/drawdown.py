from datetime import date


def compute_drawdown_features(prefix: str, prices: list[float], dates: list[date],
                               params: dict) -> dict[str, float]:
    results: dict[str, float] = {}
    if len(prices) < 2:
        return results

    for w in [60, 120, 252]:
        if len(prices) >= w:
            peak = max(prices[-w:])
            dd = (prices[-1] - peak) / peak
            results[f"{prefix}_drawdown_{w}d"] = dd

    peak = prices[0]
    max_dd = 0.0
    dd_duration = 0
    current_dd_duration = 0
    for p in prices[1:]:
        peak = max(peak, p)
        dd = (p - peak) / peak
        max_dd = min(max_dd, dd)
        if dd < 0:
            current_dd_duration += 1
        else:
            dd_duration = max(dd_duration, current_dd_duration)
            current_dd_duration = 0
    dd_duration = max(dd_duration, current_dd_duration)

    results[f"{prefix}_max_drawdown"] = max_dd
    results[f"{prefix}_drawdown_duration"] = float(dd_duration)

    return results

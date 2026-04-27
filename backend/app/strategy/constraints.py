def apply_concentration_limit(portfolio: list[dict], max_weight: float = 0.30) -> list[dict]:
    for p in portfolio:
        if p["target_weight"] > max_weight:
            excess = p["target_weight"] - max_weight
            p["target_weight"] = max_weight
            n_others = len(portfolio) - 1
            if n_others > 0:
                distrib = excess / n_others
                for other in portfolio:
                    if other.get("instrument_id") != p.get("instrument_id"):
                        other["target_weight"] += distrib
    return portfolio


def apply_turnover_limit(portfolio: list[dict], prev_weights: dict,
                         max_turnover: float = 0.50) -> list[dict]:
    total_move = sum(
        abs(p["target_weight"] - prev_weights.get(p.get("instrument_id"), 0))
        for p in portfolio
    )
    half_turnover = total_move / 2
    if half_turnover > max_turnover:
        scale = max_turnover / half_turnover
        for p in portfolio:
            prev_w = prev_weights.get(p.get("instrument_id"), 0)
            p["target_weight"] = prev_w + (p["target_weight"] - prev_w) * scale
    return portfolio


def apply_min_positions(portfolio: list[dict], min_count: int = 3) -> list[dict]:
    non_zero = [p for p in portfolio if p["target_weight"] > 0.01]
    if len(non_zero) < min_count:
        for p in portfolio:
            if p["target_weight"] < 0.01:
                p["target_weight"] = 0.01
    return portfolio


def apply_max_drawdown_check(portfolio: list[dict], instrument_drawdowns: dict,
                              max_dd: float = -0.15) -> list[dict]:
    for p in portfolio:
        dd = instrument_drawdowns.get(p.get("instrument_id"), 0)
        if dd < max_dd:
            p["target_weight"] = 0.0
    return portfolio

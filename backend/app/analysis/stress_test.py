from __future__ import annotations

import numpy as np
from typing import Any


# Predefined stress test scenarios for A-share markets
DEFAULT_SCENARIOS = [
    {
        "name": "Market Crash (-20%)",
        "description": "Broad market decline of 20%",
        "shocks": {"__market__": -0.20},
    },
    {
        "name": "Moderate Correction (-10%)",
        "description": "Moderate market correction of 10%",
        "shocks": {"__market__": -0.10},
    },
    {
        "name": "Sector Rotation",
        "description": "Technology up 10%, Finance down 15%",
        "shocks": {"__market__": 0.0, "technology": 0.10, "finance": -0.15},
    },
    {
        "name": "Interest Rate Spike",
        "description": "Rates rise sharply: bonds down 8%, equities down 5%",
        "shocks": {"__market__": -0.05, "bond": -0.08},
    },
    {
        "name": "Black Swan (-30%)",
        "description": "Extreme event with 30% market decline",
        "shocks": {"__market__": -0.30},
    },
    {
        "name": "Recovery Rally (+15%)",
        "description": "Market recovery with 15% gain",
        "shocks": {"__market__": 0.15},
    },
]


def run_stress_test(
    portfolio_value: float,
    positions: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run stress test scenarios on a portfolio.

    Args:
        portfolio_value: Current total portfolio value.
        positions: List of position dicts with keys:
            - symbol: Instrument symbol/identifier
            - value: Current market value of the position
            - sector: (optional) Sector classification
        scenarios: List of scenario dicts with keys:
            - name: Scenario name
            - description: (optional) Scenario description
            - shocks: Dict mapping symbol/sector/__market__ to shock magnitude

    Returns:
        List of result dicts, one per scenario.
    """
    results = []

    for scenario in scenarios:
        scenario_shocks = scenario.get("shocks", {})
        market_shock = scenario_shocks.get("__market__", 0.0)

        shocked_value = portfolio_value
        position_impacts = []

        for pos in positions:
            symbol = pos["symbol"]
            value = pos["value"]
            sector = pos.get("sector", "")

            # Priority: symbol-specific > sector > market
            shock = scenario_shocks.get(
                symbol,
                scenario_shocks.get(sector, market_shock),
            )

            impact = value * shock
            shocked_value += impact

            position_impacts.append({
                "symbol": symbol,
                "original_value": value,
                "shock": shock,
                "impact": impact,
            })

        loss = shocked_value - portfolio_value
        results.append({
            "scenario": scenario["name"],
            "description": scenario.get("description", ""),
            "original_value": portfolio_value,
            "shocked_value": shocked_value,
            "loss": loss,
            "loss_pct": loss / portfolio_value if portfolio_value > 0 else 0.0,
            "position_impacts": position_impacts,
        })

    return results


def run_historical_stress_test(
    portfolio_value: float,
    positions: list[dict[str, Any]],
    historical_returns: dict[str, list[float]],
    lookback_days: int = 5,
) -> list[dict[str, Any]]:
    """Run stress test using worst historical return windows.

    Args:
        portfolio_value: Current total portfolio value.
        positions: List of position dicts with symbol/value keys.
        historical_returns: Dict mapping symbol to list of daily returns.
        lookback_days: Number of days in the stress window.

    Returns:
        List of stress test results based on historical worst periods.
    """
    results = []

    # Find the worst lookback_days window for each symbol
    for pos in positions:
        symbol = pos["symbol"]
        returns = historical_returns.get(symbol, [])
        if len(returns) < lookback_days:
            continue

        # Find worst cumulative return over lookback_days
        worst_cum = 0.0
        worst_end = 0
        for i in range(len(returns) - lookback_days + 1):
            window = returns[i : i + lookback_days]
            cum = float(np.prod([1 + r for r in window]) - 1)
            if cum < worst_cum:
                worst_cum = cum
                worst_end = i + lookback_days

        if worst_cum < 0:
            impact = pos["value"] * worst_cum
            results.append({
                "scenario": f"Worst {lookback_days}-day decline for {symbol}",
                "symbol": symbol,
                "original_value": portfolio_value,
                "shocked_value": portfolio_value + impact,
                "loss": impact,
                "loss_pct": impact / portfolio_value if portfolio_value > 0 else 0.0,
                "worst_return": worst_cum,
                "worst_period_end_index": worst_end,
            })

    # Sort by loss magnitude
    results.sort(key=lambda r: r["loss"])
    return results


def get_default_scenarios() -> list[dict[str, Any]]:
    """Return the predefined stress test scenarios."""
    return DEFAULT_SCENARIOS.copy()

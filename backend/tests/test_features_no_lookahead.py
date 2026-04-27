"""No-lookahead tests: feature functions are pure functions of their inputs.

The real lookahead guarantee is in FeatureRegistry.compute_all(), which filters
bars by trade_date <= as_of_date. These tests verify the feature functions are
deterministic (same input → same output) and handle edge cases without crashing.
"""
from datetime import date, timedelta
from app.features.trend import compute_trend_features
from app.features.momentum import compute_momentum_features
from app.features.volatility import compute_volatility_features
from app.features.drawdown import compute_drawdown_features
from app.features.liquidity import compute_liquidity_features


def test_feature_determinism():
    """Same price/date arrays must always produce identical features."""
    prices = [1.0 + i * 0.01 for i in range(200)]
    volumes = [1000000.0 + i * 1000 for i in range(200)]
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(200)]

    r1 = compute_trend_features("t", prices, dates, {})
    r2 = compute_trend_features("t", prices, dates, {})
    assert r1 == r2

    r1 = compute_momentum_features("m", prices, dates, {})
    r2 = compute_momentum_features("m", prices, dates, {})
    assert r1 == r2


def test_features_with_limited_data():
    """Features with insufficient data return empty dicts, never crash."""
    prices = [1.0, 2.0]
    dates = [date(2024, 1, 1), date(2024, 1, 2)]
    volumes = [1000.0, 2000.0]

    for fn in [
        compute_trend_features,
        compute_momentum_features,
        compute_volatility_features,
        compute_drawdown_features,
    ]:
        result = fn("x", prices, dates, {})
        assert isinstance(result, dict)

    result = compute_liquidity_features("x", volumes, dates, {})
    assert isinstance(result, dict)


def test_features_with_empty_data():
    """Empty arrays must return empty dicts."""
    fns = [
        compute_trend_features,
        compute_momentum_features,
        compute_volatility_features,
        compute_drawdown_features,
    ]
    for fn in fns:
        assert fn("x", [], [], {}) == {}
    assert compute_liquidity_features("x", [], [], {}) == {}

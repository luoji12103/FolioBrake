from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.base import get_db
from app.data.models import Instrument

router = APIRouter(tags=["analysis"])


def _fetch_prices(db, symbol: str):
    inst = db.execute(select(Instrument).where(Instrument.symbol == symbol)).scalar_one_or_none()
    if not inst:
        return None, [], []
    from app.data.models import DailyBar
    bars = list(db.execute(
        select(DailyBar).where(DailyBar.instrument_id == inst.id).order_by(DailyBar.trade_date)
    ).scalars().all())
    return inst, [b.close for b in bars], [str(b.trade_date) for b in bars]


VALID_INDICATORS = {"sma", "ema", "rsi", "macd", "bollinger", "volatility", "drawdown", "correlation"}


@router.get("/indicators/{symbol}")
def get_indicators(
    symbol: str,
    indicator: str = Query(..., max_length=64),
    window: int = Query(20, ge=2, le=500),
    db: Session = Depends(get_db),
):
    from app.analysis.indicators import compute_ma, compute_ema, compute_rsi, compute_macd, compute_bollinger_bands
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 2:
        return {"error": "Insufficient price data"}

    base_indicator = indicator.split("_")[0] if "_" in indicator else indicator
    if base_indicator not in VALID_INDICATORS:
        return {"error": f"Unknown indicator: {indicator}"}

    if indicator.startswith("sma_"):
        w = int(indicator.split("_")[1]) if "_" in indicator else window
        values = compute_ma(prices, w)
    elif indicator.startswith("ema_"):
        w = int(indicator.split("_")[1]) if "_" in indicator else window
        values = compute_ema(prices, w)
    elif indicator == "rsi":
        values = compute_rsi(prices, period=window)
    elif indicator == "macd":
        values = compute_macd(prices)
    elif indicator == "bollinger":
        values = compute_bollinger_bands(prices, window=window)
    else:
        values = compute_ma(prices, window)

    return {"symbol": symbol, "indicator": indicator, "dates": dates, "values": values}


@router.get("/risk-metrics/{symbol}")
def get_risk_metrics(
    symbol: str,
    db: Session = Depends(get_db),
):
    from app.analysis.risk_metrics import compute_risk_metrics_summary
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient data for risk metrics (need 30+ points)"}
    metrics = compute_risk_metrics_summary(prices)
    return {"symbol": symbol, "metrics": metrics}


@router.get("/stress-test/{symbol}")
def get_stress_test(
    symbol: str,
    db: Session = Depends(get_db),
):
    from app.analysis.stress_test import run_stress_test, get_default_scenarios
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient data for stress testing"}
    scenarios = get_default_scenarios()
    results = run_stress_test(prices[-1], [{"symbol": symbol, "value": prices[-1]}], scenarios)
    return {"symbol": symbol, "scenarios": results}


@router.get("/monte-carlo/{symbol}")
def get_monte_carlo(
    symbol: str,
    simulations: int = Query(1000, ge=100, le=10000),
    horizon: int = Query(252, ge=5, le=1000),
    db: Session = Depends(get_db),
):
    from app.analysis.monte_carlo import run_monte_carlo
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient data for Monte Carlo simulation"}
    result = run_monte_carlo(prices, num_simulations=simulations, num_days=horizon)
    return {"symbol": symbol, "simulations": simulations, "horizon": horizon, "result": result}


@router.get("/microstructure/{symbol}")
def get_microstructure(
    symbol: str,
    window: int = Query(20, ge=5, le=252),
    db: Session = Depends(get_db),
):
    from app.analysis.microstructure import compute_realized_volatility
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < window:
        return {"error": f"Insufficient data (need {window}+ points)"}
    vol = compute_realized_volatility(prices, window=window)
    return {"symbol": symbol, "realized_volatility": vol}

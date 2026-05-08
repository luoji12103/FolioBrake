from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import get_db
from app.data.models import DailyBar, Instrument
from app.analysis.indicators import (
    compute_ma,
    compute_ema,
    compute_rsi,
    compute_macd,
    compute_bollinger_bands,
    compute_volatility_series,
    compute_drawdown_series,
    compute_correlation_matrix,
    compute_return_attribution,
)
from app.analysis.risk_metrics import (
    compute_var,
    compute_cvar,
    compute_var_historical,
    compute_var_parametric,
    compute_var_cornish_fisher,
    compute_risk_metrics_summary,
)
from app.analysis.stress_test import (
    run_stress_test,
    get_default_scenarios,
)
from app.analysis.monte_carlo import (
    run_monte_carlo,
    run_monte_carlo_var,
)
from app.analysis.microstructure import (
    compute_realized_volatility,
)

router = APIRouter(tags=["analysis"])


def _fetch_prices(db: Session, symbol: str) -> tuple[Instrument | None, list[float], list[str]]:
    inst = db.execute(
        select(Instrument).where(Instrument.symbol == symbol)
    ).scalar_one_or_none()
    if not inst:
        return None, [], []

    bars = list(
        db.execute(
            select(DailyBar)
            .where(DailyBar.instrument_id == inst.id)
            .order_by(DailyBar.trade_date)
        ).scalars().all()
    )

    prices = [b.close for b in bars]
    dates = [str(b.trade_date) for b in bars]
    return inst, prices, dates



@router.get("/indicators/{symbol}")
def get_indicators(
    symbol: str,
    indicator: str = Query(..., description="Indicator name: sma_N, ema_N, rsi, macd, bollinger"),
    window: int = Query(20, description="Window/period parameter"),
    db: Session = Depends(get_db),
):
    """Compute technical indicator for a symbol."""
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 2:
        return {"error": "Insufficient price data"}

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
        return {"error": f"Unknown indicator: {indicator}"}

    return {"symbol": symbol, "indicator": indicator, "dates": dates, "values": values}



@router.get("/correlation")
def get_correlation_matrix(db: Session = Depends(get_db)):
    """Compute correlation matrix for all instruments."""
    instruments = list(db.execute(select(Instrument)).scalars().all())

    price_data: dict[str, list[float]] = {}
    for inst in instruments:
        bars = list(
            db.execute(
                select(DailyBar)
                .where(DailyBar.instrument_id == inst.id)
                .order_by(DailyBar.trade_date)
            ).scalars().all()
        )
        if bars:
            price_data[inst.symbol] = [b.close for b in bars]

    result = compute_correlation_matrix(price_data)
    return result



@router.get("/volatility/{symbol}")
def get_volatility(
    symbol: str,
    window: int = Query(20, description="Rolling window in days"),
    db: Session = Depends(get_db),
):
    """Compute rolling volatility time series for a symbol."""
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < window + 1:
        return {"error": "Insufficient price data"}

    vol_series = compute_volatility_series(prices, window=window)

    return {
        "symbol": symbol,
        "window": window,
        "dates": dates,
        "volatility": vol_series,
    }



@router.get("/drawdown/{symbol}")
def get_drawdown(symbol: str, db: Session = Depends(get_db)):
    """Compute drawdown time series for a symbol."""
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 2:
        return {"error": "Insufficient price data"}

    dd_data = compute_drawdown_series(prices)

    max_dd = min(dd_data["drawdown"]) if dd_data["drawdown"] else 0.0
    current_dd = dd_data["drawdown"][-1] if dd_data["drawdown"] else 0.0

    return {
        "symbol": symbol,
        "dates": dates,
        "drawdown": dd_data["drawdown"],
        "peak": dd_data["peak"],
        "max_drawdown": max_dd,
        "current_drawdown": current_dd,
    }



@router.get("/attribution/{symbol}")
def get_return_attribution(
    symbol: str,
    benchmark: str = Query(..., description="Benchmark symbol"),
    db: Session = Depends(get_db),
):
    """Compute return attribution for symbol vs benchmark."""
    _, portfolio_prices, dates = _fetch_prices(db, symbol)
    if not portfolio_prices:
        return {"error": f"Instrument not found: {symbol}"}

    _, benchmark_prices, _ = _fetch_prices(db, benchmark)
    if not benchmark_prices:
        return {"error": f"Benchmark not found: {benchmark}"}

    # Compute daily returns
    import numpy as np

    p_arr = np.array(portfolio_prices)
    b_arr = np.array(benchmark_prices)

    p_returns = (np.diff(p_arr) / p_arr[:-1]).tolist()
    b_returns = (np.diff(b_arr) / b_arr[:-1]).tolist()

    result = compute_return_attribution(p_returns, b_returns)
    result["symbol"] = symbol
    result["benchmark"] = benchmark
    result["dates"] = dates[1:]

    return result


import numpy as np


@router.get("/var/{symbol}")
def get_var(
    symbol: str,
    confidence: float = Query(0.95, description="Confidence level (e.g. 0.95)"),
    db: Session = Depends(get_db),
):
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient price data (need >= 30 observations)"}

    returns = (np.diff(prices) / prices[:-1]).tolist()

    return {
        "symbol": symbol,
        "confidence": confidence,
        "var": compute_var(returns, confidence),
        "cvar": compute_cvar(returns, confidence),
        "var_historical": compute_var_historical(returns, confidence),
        "var_parametric": compute_var_parametric(returns, confidence),
        "var_cornish_fisher": compute_var_cornish_fisher(returns, confidence),
    }


@router.get("/risk-summary/{symbol}")
def get_risk_summary(
    symbol: str,
    confidence: float = Query(0.95),
    db: Session = Depends(get_db),
):
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient price data (need >= 30 observations)"}

    returns = (np.diff(prices) / prices[:-1]).tolist()
    return compute_risk_metrics_summary(returns, confidence)


class StressTestRequest(BaseModel):
    portfolio_value: float
    positions: list[dict]
    scenarios: list[dict] | None = None


@router.post("/stress-test")
def run_stress_test_endpoint(req: StressTestRequest):
    scenarios = req.scenarios if req.scenarios else get_default_scenarios()
    results = run_stress_test(req.portfolio_value, req.positions, scenarios)
    return {"results": results, "num_scenarios": len(results)}


@router.get("/stress-test/defaults")
def get_default_stress_scenarios():
    return {"scenarios": get_default_scenarios()}


@router.get("/monte-carlo/{symbol}")
def get_monte_carlo(
    symbol: str,
    num_simulations: int = Query(1000, ge=100, le=50000),
    num_days: int = Query(252, ge=1, le=1260),
    db: Session = Depends(get_db),
):
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient price data (need >= 30 observations)"}

    returns = (np.diff(prices) / prices[:-1]).tolist()
    result = run_monte_carlo(returns, num_simulations, num_days)
    return {"symbol": symbol, **result}


@router.get("/monte-carlo-var/{symbol}")
def get_monte_carlo_var(
    symbol: str,
    portfolio_value: float = Query(..., description="Current portfolio value"),
    num_simulations: int = Query(10000, ge=100, le=100000),
    horizon_days: int = Query(10, ge=1, le=252),
    confidence: float = Query(0.95),
    db: Session = Depends(get_db),
):
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < 30:
        return {"error": "Insufficient price data (need >= 30 observations)"}

    returns = (np.diff(prices) / prices[:-1]).tolist()
    result = run_monte_carlo_var(returns, portfolio_value, num_simulations, horizon_days, confidence)
    return {"symbol": symbol, **result}


@router.get("/realized-volatility/{symbol}")
def get_realized_volatility(
    symbol: str,
    window: int = Query(20, ge=2, le=252),
    db: Session = Depends(get_db),
):
    inst, prices, dates = _fetch_prices(db, symbol)
    if not inst:
        return {"error": "Instrument not found"}
    if len(prices) < window + 2:
        return {"error": "Insufficient price data"}

    result = compute_realized_volatility(prices, window)
    return {"symbol": symbol, "dates": dates[window + 1:], **result}

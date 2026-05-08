from __future__ import annotations

from datetime import datetime, date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.adapter import AKShareAdapter
from app.data.models import DailyBar, Instrument
from app.data.sync import DataSyncService
from app.db.base import get_db

router = APIRouter(tags=["data"])


# ---------------------------------------------------------------------------
# Request / Response schemas (Pydantic v2)
# ---------------------------------------------------------------------------

class SyncRequest(BaseModel):
    """Payload for POST /data/sync."""

    symbols: list[str] = Field(
        ..., min_length=1, description="ETF symbols to sync, e.g. ['510050']"
    )
    start_date: str = Field(
        default="20240101",
        pattern=r"^\d{8}$",
        description="Start date in YYYYMMDD format",
    )
    end_date: str = Field(
        default="20260331",
        pattern=r"^\d{8}$",
        description="End date in YYYYMMDD format",
    )


class InstrumentOut(BaseModel):
    id: int
    symbol: str
    name: str
    exchange: str
    type: str
    category: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BarOut(BaseModel):
    trade_date: date_type = Field(serialization_alias="date")
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    adj_close: Optional[float] = None

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_serializer("trade_date")
    def serialize_trade_date(self, v: date_type) -> str:
        return v.isoformat()


class SyncSummary(BaseModel):
    symbols_processed: int
    total_bars_synced: int
    details: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/sync", response_model=SyncSummary)
def sync_data(
    payload: SyncRequest,
    db: Session = Depends(get_db),
) -> SyncSummary:
    """Sync daily bars for one or more ETF symbols."""
    service = DataSyncService(db)
    details: list[dict] = []
    total_bars = 0

    for symbol in payload.symbols:
        try:
            inst = service.sync_instrument(symbol)
            db.commit()  # persist instrument even if data fetch fails
            count = service.sync_daily_bars(
                inst.id, payload.start_date, payload.end_date
            )
            details.append({"symbol": symbol, "instrument_id": inst.id, "bars": count})
            total_bars += count
        except Exception as exc:
            details.append(
                {"symbol": symbol, "instrument_id": None, "bars": 0, "error": str(exc)}
            )

    return SyncSummary(
        symbols_processed=len(payload.symbols),
        total_bars_synced=total_bars,
        details=details,
    )


@router.get("/instruments", response_model=list[InstrumentOut])
def list_instruments(db: Session = Depends(get_db)) -> list[Instrument]:
    """Return all instruments in the database."""
    stmt = select(Instrument).order_by(Instrument.symbol)
    return list(db.execute(stmt).scalars().all())


class AddInstrumentRequest(BaseModel):
    symbol: str


@router.post("/instruments", response_model=InstrumentOut)
def add_instrument(req: AddInstrumentRequest, db: Session = Depends(get_db)):
    """Add a new ETF instrument and sync its data."""
    service = DataSyncService(db)
    inst = service.sync_instrument(req.symbol)
    db.commit()
    service.sync_daily_bars(inst.id, "20220101", "20260427")
    db.commit()
    return inst


@router.get("/bars/{symbol}", response_model=list[BarOut])
def get_bars(
    symbol: str,
    start_date: str = Query(default="20240101", pattern=r"^\d{8}$"),
    end_date: str = Query(default="20260331", pattern=r"^\d{8}$"),
    db: Session = Depends(get_db),
) -> list[DailyBar]:
    """Return daily bars for a given ETF symbol."""
    adapter = AKShareAdapter()
    normalised = adapter.normalize_symbol(symbol)

    stmt = (
        select(DailyBar)
        .join(Instrument)
        .where(Instrument.symbol == normalised)
        .where(DailyBar.trade_date >= _parse_date_param(start_date))
        .where(DailyBar.trade_date <= _parse_date_param(end_date))
        .order_by(DailyBar.trade_date)
    )
    rows = db.execute(stmt).scalars().all()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No bars found for symbol={normalised} in [{start_date}, {end_date}]",
        )
    return list(rows)


@router.get("/quality/{symbol}")
def get_quality(symbol: str, db: Session = Depends(get_db)):
    """Compute data quality check for a given ETF symbol."""
    normalised = symbol.strip().zfill(6)
    inst = db.execute(select(Instrument).where(Instrument.symbol == normalised)).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument {normalised} not found.")

    bars = list(db.execute(
        select(DailyBar).where(DailyBar.instrument_id == inst.id).order_by(DailyBar.trade_date)
    ).scalars().all())

    if not bars:
        return {
            "symbol": normalised,
            "bars_count": 0,
            "date_range_start": None,
            "date_range_end": None,
            "missing_dates": 0,
            "status": "ERROR",
            "issues": ["No bars found for this instrument"],
        }

    dates = [b.trade_date for b in bars]
    date_range_start = dates[0].isoformat()
    date_range_end = dates[-1].isoformat()

    # Check for gaps (weekdays only)
    missing = 0
    issues = []
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i-1]).days
        if diff > 3:  # More than a weekend gap
            missing += diff - 1

    # Check for zero volume
    zero_vol = sum(1 for b in bars if b.volume == 0)
    if zero_vol > 0:
        issues.append(f"{zero_vol} bars with zero volume")

    # Check for price jumps (>10% daily)
    jumps = 0
    for i in range(1, len(bars)):
        if bars[i-1].close > 0:
            change = abs(bars[i].close - bars[i-1].close) / bars[i-1].close
            if change > 0.10:
                jumps += 1
    if jumps > 0:
        issues.append(f"{jumps} price jumps (>10% daily)")

    status = "OK"
    if missing > 5 or zero_vol > 10 or jumps > 3:
        status = "WARNING"
    if missing > 20 or zero_vol > 50:
        status = "ERROR"

    return {
        "symbol": normalised,
        "bars_count": len(bars),
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
        "missing_dates": missing,
        "status": status,
        "issues": issues,
    }


@router.get("/health")
def get_data_health(db: Session = Depends(get_db)):
    """Return data source health and quality metrics."""
    from sqlalchemy import func
    
    # Count instruments
    total_instruments = db.execute(select(func.count(Instrument.id))).scalar() or 0
    
    # Get latest bar date
    latest_bar = db.execute(
        select(DailyBar.trade_date).order_by(DailyBar.trade_date.desc()).limit(1)
    ).scalar_one_or_none()
    
    # Count total bars
    total_bars = db.execute(select(func.count(DailyBar.id))).scalar() or 0
    
    # Count instruments with recent data (within 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.now().date() - timedelta(days=7)
    instruments_with_recent = db.execute(
        select(func.count(func.distinct(DailyBar.instrument_id)))
        .where(DailyBar.trade_date >= week_ago)
    ).scalar() or 0
    
    # Count stale instruments (no data in last 7 days)
    stale_instruments = total_instruments - instruments_with_recent
    
    return {
        "sources": [
            {
                "name": "akshare",
                "status": "healthy" if total_bars > 0 else "no_data",
                "instruments_count": total_instruments,
                "bars_count": total_bars
            }
        ],
        "data_quality": {
            "total_instruments": total_instruments,
            "instruments_with_gaps": stale_instruments,
            "latest_bar_date": str(latest_bar) if latest_bar else None,
            "stale_instruments": stale_instruments
        }
    }


@router.get("/sources")
def get_data_sources(db: Session = Depends(get_db)):
    """Return data source health status."""
    sources = [
        {"name": "efinance", "status": "available", "note": "Primary fallback, ETF fund quotes"},
        {"name": "akshare", "status": "rate_limited", "note": "东方财富 API rate-limited"},
    ]
    from app.data.tushare_adapter import TushareAdapter
    ts = TushareAdapter()
    sources.append({
        "name": "tushare",
        "status": "available" if ts.available else "not_configured",
        "note": "Requires TUSHARE_TOKEN env var" if not ts.available else "Token configured",
    })

    # Data freshness
    from sqlalchemy import func
    freshness = list(db.execute(
        select(
            Instrument.symbol,
            func.max(DailyBar.trade_date).label("last_date"),
            func.count(DailyBar.id).label("bar_count"),
        )
        .join(DailyBar, DailyBar.instrument_id == Instrument.id)
        .group_by(Instrument.symbol)
    ).all())

    return {
        "sources": sources,
        "freshness": [
            {"symbol": f.symbol, "last_date": str(f.last_date), "bar_count": f.bar_count}
            for f in freshness
        ],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date_param(raw: str) -> datetime:
    """Parse a YYYYMMDD query parameter into a datetime (start-of-day)."""
    return datetime.strptime(raw, "%Y%m%d")

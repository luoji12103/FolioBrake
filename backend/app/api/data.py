from __future__ import annotations

from datetime import datetime, date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.adapter import AKShareAdapter
from app.data.models import DailyBar, DataQualityReport, Instrument
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
    trade_date: date_type
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    adj_close: Optional[float] = None

    model_config = {"from_attributes": True}

    @field_serializer("trade_date")
    def serialize_trade_date(self, v: date_type) -> str:
        return v.isoformat()


class QualityReportOut(BaseModel):
    id: int
    instrument_id: int
    check_date: datetime
    missing_dates: Optional[list[str]] = None
    price_jumps: Optional[list[dict]] = None
    zero_volume_dates: Optional[list[str]] = None
    overall_status: str

    model_config = {"from_attributes": True}


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


@router.get("/quality/{symbol}", response_model=QualityReportOut)
def get_quality_report(
    symbol: str,
    db: Session = Depends(get_db),
) -> DataQualityReport:
    """Return the most recent DataQualityReport for *symbol*."""
    adapter = AKShareAdapter()
    normalised = adapter.normalize_symbol(symbol)

    inst = db.execute(
        select(Instrument).where(Instrument.symbol == normalised)
    ).scalar_one_or_none()

    if inst is None:
        raise HTTPException(status_code=404, detail=f"Instrument {normalised} not found.")

    report = db.execute(
        select(DataQualityReport)
        .where(DataQualityReport.instrument_id == inst.id)
        .order_by(DataQualityReport.check_date.desc())
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"No quality report found for symbol={normalised}",
        )
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date_param(raw: str) -> datetime:
    """Parse a YYYYMMDD query parameter into a datetime (start-of-day)."""
    return datetime.strptime(raw, "%Y%m%d")

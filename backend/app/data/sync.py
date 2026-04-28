from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.data.adapter import AKShareAdapter
from app.data.models import DataQualityReport, DailyBar, Instrument
from app.data.quality import DataQualityChecker

logger = logging.getLogger(__name__)


class DataSyncService:
    """Orchestrates data ingestion: instruments, daily bars, quality checks."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.adapter = AKShareAdapter()
        self.quality = DataQualityChecker()

    # ------------------------------------------------------------------
    # Instrument
    # ------------------------------------------------------------------

    def sync_instrument(self, symbol: str) -> Instrument:
        """Look up an Instrument by *symbol* or create it on first encounter.

        The symbol is normalised before lookup.
        """
        symbol = self.adapter.normalize_symbol(symbol)

        stmt = select(Instrument).where(Instrument.symbol == symbol)
        inst = self.db.execute(stmt).scalar_one_or_none()

        if inst is not None:
            logger.debug("Instrument %s already exists (id=%s).", symbol, inst.id)
            return inst

        # Build a new Instrument with sensible defaults
        exchange = "SH" if symbol.startswith(("5", "6", "9")) else "SZ"
        inst = Instrument(
            symbol=symbol,
            name=symbol,  # caller can update later
            exchange=exchange,
            type="ETF",
            category=None,
        )
        self.db.add(inst)
        self.db.flush()  # populate inst.id
        logger.info("Created instrument id=%s symbol=%s.", inst.id, symbol)
        return inst

    # ------------------------------------------------------------------
    # Daily bars
    # ------------------------------------------------------------------

    def sync_daily_bars(
        self, instrument_id: int, start: str, end: str
    ) -> int:
        """Fetch OHLCV bars from the data source and upsert into *daily_bars*.

        Args:
            instrument_id: FK to instruments table.
            start: Start date in ``YYYYMMDD`` format.
            end: End date in ``YYYYMMDD`` format.

        Returns:
            Number of bars inserted or updated.
        """
        # Resolve the instrument symbol for the adapter call
        inst = self.db.get(Instrument, instrument_id)
        if inst is None:
            raise ValueError(f"Instrument id={instrument_id} not found.")

        records = self.adapter.fetch_etf_daily(inst.symbol, start, end)
        if not records:
            from app.data.efinance_adapter import EfinanceAdapter
            ef_adapter = EfinanceAdapter()
            records = ef_adapter.fetch_etf_daily(inst.symbol, start, end)
            if records:
                logger.info("Using efinance fallback for %s", inst.symbol)
        if not records:
            return 0

        inserted = 0
        for rec in records:
            trade_date_str = rec.get("trade_date")
            if trade_date_str is None:
                continue

            trade_date = _parse_date(trade_date_str)
            if trade_date is None:
                continue

            values: dict[str, Any] = {
                "instrument_id": instrument_id,
                "trade_date": trade_date,
                "open": rec.get("open"),
                "high": rec.get("high"),
                "low": rec.get("low"),
                "close": rec.get("close"),
                "volume": rec.get("volume"),
                "amount": rec.get("amount"),
                "adj_close": rec.get("adj_close"),
                "data_source": "akshare",
            }

            stmt = (
                insert(DailyBar)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["instrument_id", "trade_date"],
                    set_={
                        "open": values["open"],
                        "high": values["high"],
                        "low": values["low"],
                        "close": values["close"],
                        "volume": values["volume"],
                        "amount": values["amount"],
                        "adj_close": values["adj_close"],
                        "data_source": values["data_source"],
                        "fetched_at": datetime.utcnow(),
                    },
                )
            )
            self.db.execute(stmt)
            inserted += 1

        self.db.commit()
        logger.info(
            "Synced %d bars for instrument_id=%s (%s – %s).",
            inserted,
            instrument_id,
            start,
            end,
        )
        return inserted

    # ------------------------------------------------------------------
    # Quality check
    # ------------------------------------------------------------------

    def run_quality_check(self, instrument_id: int) -> DataQualityReport:
        """Run all data-quality checks for an instrument and persist the report."""
        inst = self.db.get(Instrument, instrument_id)
        if inst is None:
            raise ValueError(f"Instrument id={instrument_id} not found.")

        # Load bars from DB as plain dicts
        stmt = select(DailyBar).where(
            DailyBar.instrument_id == instrument_id
        ).order_by(DailyBar.trade_date)
        rows = self.db.execute(stmt).scalars().all()

        bar_dicts: list[dict[str, Any]] = []
        for r in rows:
            bar_dicts.append(
                {
                    "trade_date": r.trade_date,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "amount": r.amount,
                }
            )

        # Load trading calendar
        calendar = self.adapter.fetch_trading_calendar()

        result = self.quality.run_all(instrument_id, bar_dicts, calendar)

        report = DataQualityReport(
            instrument_id=instrument_id,
            check_date=datetime.utcnow(),
            missing_dates=result["missing_dates"],
            price_jumps=result["price_jumps"],
            zero_volume_dates=result["zero_volume_dates"],
            overall_status=result["overall_status"],
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        logger.info(
            "Quality report id=%s created for instrument_id=%s (status=%s).",
            report.id,
            instrument_id,
            report.overall_status,
        )
        return report


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_date(raw: Any) -> date | None:
    """Parse a date from various AKShare return shapes."""
    if isinstance(raw, date):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    s = str(raw).strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    logger.warning("Could not parse date string: %s", raw)
    return None

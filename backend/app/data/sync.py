from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.data.adapter import AKShareAdapter
from app.data.models import DataQualityReport, DailyBar, Instrument
from app.data.quality import DataQualityChecker
from app.data.source_manager import DataSourceManager, get_source_manager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory sync progress tracker
# ---------------------------------------------------------------------------

class SyncProgressTracker:
    """Thread-safe in-memory store for sync progress per instrument."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # instrument_id -> { progress, total, synced, status, started_at, updated_at }
        self._store: dict[int, dict[str, Any]] = {}

    def start(self, instrument_id: int, total: int) -> None:
        with self._lock:
            self._store[instrument_id] = {
                "progress": 0,
                "total": total,
                "synced": 0,
                "status": "syncing",
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

    def update(self, instrument_id: int, synced: int) -> None:
        with self._lock:
            entry = self._store.get(instrument_id)
            if entry is None:
                return
            entry["synced"] = synced
            entry["progress"] = min(100, int(synced / max(entry["total"], 1) * 100))
            entry["updated_at"] = datetime.utcnow().isoformat()

    def finish(self, instrument_id: int, total_synced: int) -> None:
        with self._lock:
            entry = self._store.get(instrument_id)
            if entry is None:
                return
            entry["synced"] = total_synced
            entry["progress"] = 100
            entry["status"] = "done"
            entry["updated_at"] = datetime.utcnow().isoformat()

    def error(self, instrument_id: int, message: str) -> None:
        with self._lock:
            entry = self._store.get(instrument_id)
            if entry is None:
                self._store[instrument_id] = {}
                entry = self._store[instrument_id]
            entry["status"] = "error"
            entry["error"] = message
            entry["updated_at"] = datetime.utcnow().isoformat()

    def get(self, instrument_id: int) -> dict[str, Any]:
        with self._lock:
            return dict(self._store.get(instrument_id, {"progress": 0, "status": "idle"}))

    def get_all(self) -> dict[int, dict[str, Any]]:
        with self._lock:
            return {k: dict(v) for k, v in self._store.items()}


# Module-level singleton
sync_progress = SyncProgressTracker()


class DataSyncService:
    """Orchestrates data ingestion: instruments, daily bars, quality checks."""

    def __init__(self, db: Session, manager: DataSourceManager | None = None) -> None:
        self.db = db
        self.adapter = AKShareAdapter()
        self._manager = manager or get_source_manager()
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
        return self.sync_daily_bars_batch(instrument_id, start, end)

    def sync_daily_bars_batch(
        self,
        instrument_id: int,
        start: str,
        end: str,
        batch_size: int = 1000,
    ) -> int:
        inst = self.db.get(Instrument, instrument_id)
        if inst is None:
            raise ValueError(f"Instrument id={instrument_id} not found.")

        last_bar = self.db.execute(
            select(DailyBar.trade_date)
            .where(DailyBar.instrument_id == instrument_id)
            .order_by(DailyBar.trade_date.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_bar is not None:
            incremental_start = (last_bar + _ONE_DAY).strftime("%Y%m%d")
            if incremental_start > start:
                start = incremental_start
                logger.info(
                    "Incremental sync for %s: last_bar=%s, new start=%s",
                    inst.symbol, last_bar, start,
                )

        if start > end:
            logger.info("No new data to sync for %s (start=%s > end=%s).", inst.symbol, start, end)
            return 0

        records = self._fetch_with_fallback(inst.symbol, start, end)
        if not records:
            return 0

        source = self._last_source
        total = len(records)
        sync_progress.start(instrument_id, total)

        prepared: list[dict[str, Any]] = []
        for rec in records:
            trade_date = _parse_date(rec.get("trade_date"))
            if trade_date is None:
                continue
            prepared.append({
                "instrument_id": instrument_id,
                "trade_date": trade_date,
                "open": rec.get("open"),
                "high": rec.get("high"),
                "low": rec.get("low"),
                "close": rec.get("close"),
                "volume": rec.get("volume"),
                "amount": rec.get("amount"),
                "adj_close": rec.get("adj_close"),
                "data_source": source,
            })

        inserted = 0
        for i in range(0, len(prepared), batch_size):
            batch = prepared[i : i + batch_size]
            stmt = (
                insert(DailyBar)
                .values(batch)
                .on_conflict_do_update(
                    index_elements=["instrument_id", "trade_date"],
                    set_={
                        "open": DailyBar.__table__.c.open,
                        "high": DailyBar.__table__.c.high,
                        "low": DailyBar.__table__.c.low,
                        "close": DailyBar.__table__.c.close,
                        "volume": DailyBar.__table__.c.volume,
                        "amount": DailyBar.__table__.c.amount,
                        "adj_close": DailyBar.__table__.c.adj_close,
                        "data_source": DailyBar.__table__.c.data_source,
                        "fetched_at": datetime.utcnow(),
                    },
                )
            )
            self.db.execute(stmt)
            self.db.commit()
            inserted += len(batch)
            sync_progress.update(instrument_id, inserted)

        sync_progress.finish(instrument_id, inserted)
        logger.info(
            "Synced %d bars for instrument_id=%s (%s – %s).",
            inserted, instrument_id, start, end,
        )
        return inserted

    def _fetch_with_fallback(self, symbol: str, start: str, end: str) -> list[dict[str, Any]]:
        records, source_name = self._manager.fetch_etf_daily(symbol, start, end)
        self._last_source = source_name or "unknown"
        return records

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

_ONE_DAY = timedelta(days=1)


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

"""Scheduled data sync worker using APScheduler.

Runs daily ETF price updates, quality checks, and risk evaluations.
"""
import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.sync import DataSyncService
from app.data.models import Instrument, DataQualityReport
from app.db.base import SessionLocal

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["510050", "510300", "510500", "159919", "159915"]


class ScheduledSyncRunner:
    """Runs data sync and quality checks on a schedule."""

    def __init__(self):
        self.last_run: dict[str, datetime] = {}
        self.sync_history: list[dict] = []

    def run_daily_sync(self, symbols: list[str] | None = None) -> dict:
        """Sync ETF data and run quality checks."""
        db = SessionLocal()
        result = {"synced": 0, "quality_checks": 0, "errors": []}

        try:
            symbols = symbols or DEFAULT_SYMBOLS
            service = DataSyncService(db)

            for symbol in symbols:
                try:
                    inst = service.sync_instrument(symbol)
                    db.commit()
                    count = service.sync_daily_bars(
                        inst.id,
                        "20220101",
                        date.today().strftime("%Y%m%d"),
                    )
                    result["synced"] += count

                    if count > 0:
                        report = service.run_quality_check(inst.id)
                        result["quality_checks"] += 1
                except Exception as e:
                    result["errors"].append({"symbol": symbol, "error": str(e)})

        finally:
            db.close()

        self.last_run["daily_sync"] = datetime.utcnow()
        self.sync_history.append({**result, "timestamp": datetime.utcnow().isoformat()})
        logger.info("Daily sync complete: %d bars, %d quality checks", result["synced"], result["quality_checks"])
        return result

    def get_sync_status(self) -> dict:
        """Return sync health status."""
        db = SessionLocal()
        try:
            instruments = list(db.execute(select(Instrument)).scalars().all())
            status = []
            for inst in instruments:
                latest_bar = db.execute(
                    select(DataQualityReport)
                    .where(DataQualityReport.instrument_id == inst.id)
                    .order_by(DataQualityReport.check_date.desc())
                    .limit(1)
                ).scalar_one_or_none()

                status.append({
                    "symbol": inst.symbol,
                    "name": inst.name,
                    "last_quality": latest_bar.check_date.isoformat() if latest_bar else None,
                    "quality_status": latest_bar.overall_status if latest_bar else "UNKNOWN",
                })
            return {"instruments": status, "last_sync": self.last_run.get("daily_sync", "").isoformat() if self.last_run.get("daily_sync") else None}
        finally:
            db.close()

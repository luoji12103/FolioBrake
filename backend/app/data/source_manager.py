from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.data.adapter import AKShareAdapter
from app.data.efinance_adapter import EfinanceAdapter
from app.data.tushare_adapter import TushareAdapter

logger = logging.getLogger(__name__)

_RECOVERY_INTERVAL = 300


@dataclass
class SourceStatus:
    name: str
    priority: int
    healthy: bool = True
    last_check: float = 0.0
    last_failure: float = 0.0
    consecutive_failures: int = 0
    total_calls: int = 0
    total_failures: int = 0


class DataSourceManager:
    def __init__(self) -> None:
        self._adapters: dict[str, Any] = {
            "akshare": AKShareAdapter(),
            "tushare": TushareAdapter(),
            "efinance": EfinanceAdapter(),
        }
        self._statuses: list[SourceStatus] = [
            SourceStatus(name="akshare", priority=1),
            SourceStatus(name="tushare", priority=2),
            SourceStatus(name="efinance", priority=3),
        ]

    @property
    def source_names(self) -> list[str]:
        return [s.name for s in self._statuses]

    def get_adapter(self) -> tuple[Any, SourceStatus]:
        now = time.time()
        ordered = sorted(self._statuses, key=lambda s: s.priority)

        for status in ordered:
            if not status.healthy:
                if now - status.last_failure < _RECOVERY_INTERVAL:
                    logger.debug(
                        "Skipping %s (unhealthy, %.0fs until retry)",
                        status.name,
                        _RECOVERY_INTERVAL - (now - status.last_failure),
                    )
                    continue
                logger.info("Recovery interval elapsed for %s; will retry", status.name)

            return self._adapters[status.name], status

        raise RuntimeError("No healthy data sources available")

    def _get_adapters_in_order(self) -> list[tuple[Any, SourceStatus]]:
        now = time.time()
        ordered = sorted(self._statuses, key=lambda s: s.priority)
        result: list[tuple[Any, SourceStatus]] = []
        for status in ordered:
            if not status.healthy and now - status.last_failure < _RECOVERY_INTERVAL:
                continue
            result.append((self._adapters[status.name], status))
        return result

    def report_success(self, source_name: str) -> None:
        for status in self._statuses:
            if status.name == source_name:
                status.healthy = True
                status.consecutive_failures = 0
                status.total_calls += 1
                status.last_check = time.time()
                break

    def report_failure(self, source_name: str) -> None:
        for status in self._statuses:
            if status.name == source_name:
                status.consecutive_failures += 1
                status.total_failures += 1
                status.total_calls += 1
                status.last_failure = time.time()
                status.last_check = time.time()
                status.healthy = False
                logger.warning(
                    "Marked %s unhealthy after %d consecutive failure(s)",
                    source_name,
                    status.consecutive_failures,
                )
                break

    def fetch_etf_daily(
        self, symbol: str, start_date: str, end_date: str
    ) -> tuple[list[dict[str, Any]], str]:
        for adapter, status in self._get_adapters_in_order():
            try:
                logger.info(
                    "Trying %s for %s (%s–%s)", status.name, symbol, start_date, end_date
                )
                records = adapter.fetch_etf_daily(symbol, start_date, end_date)
                if records:
                    self.report_success(status.name)
                    logger.info(
                        "%s returned %d rows for %s", status.name, len(records), symbol
                    )
                    return records, status.name
                logger.info("%s returned no data for %s", status.name, symbol)
            except Exception:
                logger.exception("%s raised for %s", status.name, symbol)
                self.report_failure(status.name)

        logger.warning("All data sources exhausted for %s; returning empty", symbol)
        return [], ""

    async def health_check_all(self) -> list[dict[str, Any]]:
        probe_symbol = "510050"
        probe_start = "20240101"
        probe_end = "20240110"
        results: list[dict[str, Any]] = []

        for status in sorted(self._statuses, key=lambda s: s.priority):
            adapter = self._adapters[status.name]
            try:
                records = adapter.fetch_etf_daily(probe_symbol, probe_start, probe_end)
                status.healthy = True
                status.consecutive_failures = 0
                status.last_check = time.time()
                status.total_calls += 1
            except Exception:
                logger.exception("Health check failed for %s", status.name)
                status.healthy = False
                status.last_failure = time.time()
                status.consecutive_failures += 1
                status.total_failures += 1
                status.total_calls += 1

            results.append(self._status_dict(status))

        return results

    def get_status_snapshot(self) -> list[dict[str, Any]]:
        return [self._status_dict(s) for s in sorted(self._statuses, key=lambda x: x.priority)]

    @staticmethod
    def _status_dict(s: SourceStatus) -> dict[str, Any]:
        now = time.time()
        return {
            "name": s.name,
            "priority": s.priority,
            "healthy": s.healthy,
            "consecutive_failures": s.consecutive_failures,
            "total_calls": s.total_calls,
            "total_failures": s.total_failures,
            "last_check": s.last_check,
            "last_failure": s.last_failure,
            "seconds_since_last_check": (
                round(now - s.last_check, 1) if s.last_check else None
            ),
            "recovery_in": (
                max(0, round(_RECOVERY_INTERVAL - (now - s.last_failure), 1))
                if not s.healthy and s.last_failure
                else None
            ),
        }


_manager: DataSourceManager | None = None


def get_source_manager() -> DataSourceManager:
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
    return _manager

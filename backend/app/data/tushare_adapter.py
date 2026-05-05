"""Tushare data source adapter. Requires TUSHARE_TOKEN env var.

Mirrors the EfinanceAdapter pattern for consistent fallback behavior.
"""
import logging
import os
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class TushareAdapter:
    """Tushare-based ETF data adapter. Requires TUSHARE_TOKEN environment variable."""

    COLUMN_MAP = {
        "trade_date": "trade_date",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "vol": "volume",
        "amount": "amount",
    }

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("TUSHARE_TOKEN", "")
        self._api = None

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _get_api(self):
        if self._api is None and self.token:
            try:
                import tushare as ts
                ts.set_token(self.token)
                self._api = ts.pro_api()
                logger.info("Tushare API initialized")
            except ImportError:
                logger.warning("tushare package not installed")
            except Exception:
                logger.exception("Tushare API initialization failed")
        return self._api

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize to Tushare format: 510050.SH or 159915.SZ."""
        symbol = str(symbol).strip().zfill(6)
        if symbol.startswith(("5", "6", "9")):
            return f"{symbol}.SH"
        return f"{symbol}.SZ"

    def fetch_etf_daily(
        self, symbol: str, start_date: str = "20100101", end_date: str = "20260427"
    ) -> list[dict]:
        """Fetch ETF daily data from Tushare."""
        if not self.available:
            logger.debug("Tushare not available (no token)")
            return []

        api = self._get_api()
        if api is None:
            return []

        try:
            normalized = self.normalize_symbol(symbol)
            df: pd.DataFrame = api.fund_daily(
                ts_code=normalized,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                logger.info("Tushare returned empty data for %s", symbol)
                return []

            df = df.rename(columns=self.COLUMN_MAP)
            records = []
            for _, row in df.iterrows():
                records.append({
                    "trade_date": str(row.get("trade_date", ""))[:10],
                    "open": float(row.get("open", 0) or 0),
                    "high": float(row.get("high", 0) or 0),
                    "low": float(row.get("low", 0) or 0),
                    "close": float(row.get("close", 0) or 0),
                    "volume": float(row.get("volume", 0) or 0),
                    "amount": float(row.get("amount", 0) or 0),
                    "adj_close": None,
                })

            logger.info("Tushare: %d rows for %s", len(records), symbol)
            return records
        except Exception:
            logger.exception("Tushare fetch failed for %s", symbol)
            return []

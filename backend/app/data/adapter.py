import logging
from typing import Any

logger = logging.getLogger(__name__)

# Column name mapping from AKShare to our internal schema
_COLUMN_MAP: dict[str, str] = {
    "日期": "trade_date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
}


class AKShareAdapter:
    """Adapter for fetching market data from AKShare.

    Wraps AKShare API calls with error handling and column-name
    translation so the rest of the system works with a consistent schema.
    """

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Ensure symbol is a 6-digit string, stripping any exchange prefix.

        >>> AKShareAdapter.normalize_symbol("510050")
        '510050'
        >>> AKShareAdapter.normalize_symbol("sh510050")
        '510050'
        """
        cleaned = symbol.strip().lower()
        # Strip common exchange prefixes
        for prefix in ("sh", "sz", "bj"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                break
        # Zero-pad if shorter than 6 digits
        return cleaned.zfill(6)

    def fetch_etf_daily(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Fetch daily OHLCV bars for an ETF from AKShare.

        Args:
            symbol: 6-digit ETF code (e.g. "510050").
            start_date: Start date string in "YYYYMMDD" format.
            end_date: End date string in "YYYYMMDD" format.

        Returns:
            List of dicts with keys matching our internal schema:
            trade_date, open, high, low, close, volume, amount.
            Returns an empty list on failure.
        """
        try:
            import akshare as ak
        except ImportError:
            logger.error("AKShare is not installed; cannot fetch data.")
            return []

        try:
            raw = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="",
            )
        except Exception:
            logger.exception("AKShare call failed for symbol=%s", symbol)
            return []

        if raw is None or raw.empty:
            logger.info("AKShare returned no data for symbol=%s (%s–%s)", symbol, start_date, end_date)
            return []

        # Build a list of column names we have in the response
        available_columns = set(raw.columns)
        mapped: list[dict[str, Any]] = []
        for _, row in raw.iterrows():
            record: dict[str, Any] = {}
            for src_col, dst_col in _COLUMN_MAP.items():
                if src_col in available_columns:
                    record[dst_col] = row[src_col]
            # Only include rows that have at least a close price
            if "close" in record:
                mapped.append(record)

        logger.info(
            "Fetched %d bars for symbol=%s (%s–%s)",
            len(mapped),
            symbol,
            start_date,
            end_date,
        )
        return mapped

    @staticmethod
    def fetch_trading_calendar() -> list[str]:
        """Return a list of trading-day date strings (YYYY-MM-DD).

        Tries AKShare's tool_trade_date_hist_sina; falls back to an empty
        list when the data source is unavailable.
        """
        try:
            import akshare as ak
        except ImportError:
            logger.warning("AKShare not installed; returning empty calendar.")
            return []

        try:
            df = ak.tool_trade_date_hist_sina()
            if df is None or df.empty:
                logger.warning("AKShare returned an empty trading calendar.")
                return []

            # The column is named 'trade_date' and contains datetime or date values
            date_col = df.columns[0]
            dates: list[str] = []
            for val in df[date_col]:
                ts = getattr(val, "strftime", None)
                if ts:
                    dates.append(ts("%Y-%m-%d"))
                else:
                    dates.append(str(val)[:10])
            logger.info("Trading calendar loaded: %d days.", len(dates))
            return dates
        except Exception:
            logger.exception("Failed to fetch trading calendar from AKShare.")
            return []

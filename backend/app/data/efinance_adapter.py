"""efinance-based ETF data adapter. Works when AKShare is rate-limited."""

import logging
import pandas as pd
import efinance as ef

logger = logging.getLogger(__name__)

COLUMN_MAP = {
    "日期": "trade_date",
    "单位净值": "close",
    "累计净值": "adj_close",
    "涨跌幅": "change_pct",
}


class EfinanceAdapter:
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return str(symbol).strip().zfill(6)

    def fetch_etf_daily(self, symbol: str, start_date: str = "20100101",
                        end_date: str = "20260427") -> list[dict]:
        symbol = self.normalize_symbol(symbol)
        try:
            df: pd.DataFrame = ef.fund.get_quote_history(symbol)
            if df is None or df.empty:
                logger.warning("efinance returned empty data for %s", symbol)
                return []

            df = df.rename(columns=COLUMN_MAP)
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")

            start_fmt = _reformat_date(start_date)
            end_fmt = _reformat_date(end_date)
            df = df[(df["trade_date"] >= start_fmt) & (df["trade_date"] <= end_fmt)]

            records = []
            for _, row in df.iterrows():
                close_val = float(row.get("close", 0) or 0)
                records.append({
                    "trade_date": row["trade_date"],
                    "open": close_val,
                    "high": close_val,
                    "low": close_val,
                    "close": close_val,
                    "volume": float(row.get("volume", 0) or 0),
                    "amount": float(row.get("amount", 0) or 0),
                    "adj_close": float(row.get("adj_close", 0) or 0),
                })
            logger.info("efinance: %d rows for %s", len(records), symbol)
            return records
        except Exception:
            logger.exception("efinance failed for %s", symbol)
            return []


def _reformat_date(d: str) -> str:
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d

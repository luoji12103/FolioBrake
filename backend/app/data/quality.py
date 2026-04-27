from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Run data-quality checks against a set of daily bars and a trading calendar."""

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    @staticmethod
    def check_missing_dates(
        bars: list[dict[str, Any]], calendar: list[str]
    ) -> list[str]:
        """Return trading days from *calendar* that have no bar record.

        Args:
            bars: List of dicts; every dict must include a ``trade_date`` key.
            calendar: List of date strings in ``YYYY-MM-DD`` format.

        Returns:
            Sorted list of missing trading-day date strings.
        """
        if not calendar:
            logger.warning("No trading calendar provided; skipping missing-date check.")
            return []

        bar_dates: set[str] = set()
        for b in bars:
            td = b.get("trade_date")
            if td is None:
                continue
            # Normalise to str
            if isinstance(td, (date, datetime)):
                bar_dates.add(td.strftime("%Y-%m-%d"))
            else:
                bar_dates.add(str(td)[:10])

        calendar_set = {d[:10] for d in calendar}
        missing = sorted(calendar_set - bar_dates)
        if missing:
            logger.info("Missing %d trading dates: %s ...", len(missing), missing[:5])
        return missing

    @staticmethod
    def check_price_jumps(
        bars: list[dict[str, Any]], threshold_pct: float = 0.15
    ) -> list[dict[str, Any]]:
        """Detect day-over-day close-price jumps exceeding *threshold_pct*.

        Args:
            bars: List of dicts with *trade_date* and *close*.  The list is
                  sorted in-place by *trade_date* before analysis.
            threshold_pct: Fractional change threshold (default 0.15 = 15%).

        Returns:
            List of dicts: ``{date, pct_change, from_price, to_price}``.
        """
        if len(bars) < 2:
            return []

        # Sort by trade_date
        def _sort_key(b: dict[str, Any]) -> str:
            td = b.get("trade_date", "")
            return td if isinstance(td, str) else str(td)

        sorted_bars = sorted(bars, key=_sort_key)

        jumps: list[dict[str, Any]] = []
        for i in range(1, len(sorted_bars)):
            prev_close = sorted_bars[i - 1].get("close")
            curr_close = sorted_bars[i].get("close")
            if prev_close is None or curr_close is None or prev_close == 0:
                continue

            pct = abs(curr_close - prev_close) / abs(prev_close)
            if pct > threshold_pct:
                jumps.append(
                    {
                        "date": _sort_key(sorted_bars[i]),
                        "pct_change": round(pct, 6),
                        "from_price": prev_close,
                        "to_price": curr_close,
                    }
                )

        if jumps:
            logger.info("Detected %d price jump(s) above %.0f%%.", len(jumps), threshold_pct * 100)
        return jumps

    @staticmethod
    def check_zero_volume(bars: list[dict[str, Any]]) -> list[str]:
        """Return dates where volume equals zero.

        Args:
            bars: List of dicts with *trade_date* and *volume*.

        Returns:
            Sorted list of date strings.
        """
        zero_dates: list[str] = []
        for b in bars:
            vol = b.get("volume")
            if vol is not None and float(vol) == 0:
                td = b.get("trade_date", "")
                if isinstance(td, (date, datetime)):
                    zero_dates.append(td.strftime("%Y-%m-%d"))
                else:
                    zero_dates.append(str(td)[:10])

        if zero_dates:
            logger.info("Detected %d date(s) with zero volume.", len(zero_dates))
        return sorted(zero_dates)

    # ------------------------------------------------------------------
    # Aggregate runner
    # ------------------------------------------------------------------

    def run_all(
        self,
        instrument_id: int,
        bars: list[dict[str, Any]],
        calendar: list[str],
    ) -> dict[str, Any]:
        """Execute all quality checks and return an aggregated result.

        The returned dict matches the shape expected by ``DataQualityReport``:

        .. code-block:: python

            {
                "overall_status": "OK",        # OK | WARNING | ERROR
                "missing_dates": [...],
                "price_jumps": [...],
                "zero_volume_dates": [...],
            }
        """
        missing = self.check_missing_dates(bars, calendar)
        jumps = self.check_price_jumps(bars)
        zeros = self.check_zero_volume(bars)

        # Determine overall status
        if jumps and any(j.get("pct_change", 0) > 0.30 for j in jumps):
            status = "ERROR"
        elif missing or jumps:
            status = "WARNING"
        else:
            status = "OK"

        logger.info(
            "Quality check for instrument=%d: status=%s missing=%d jumps=%d zeros=%d",
            instrument_id,
            status,
            len(missing),
            len(jumps),
            len(zeros),
        )

        return {
            "overall_status": status,
            "missing_dates": missing,
            "price_jumps": jumps,
            "zero_volume_dates": zeros,
        }

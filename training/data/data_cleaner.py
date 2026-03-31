# training/data/data_cleaner.py

from datetime import datetime, timezone, timedelta
from app.infrastructure.monitoring.logger import setup_logger


class DataCleaner:
    """
    Cleans raw candle data before training.
    Removes duplicates, gaps, and flat candles.
    """

    M15_INTERVAL = timedelta(minutes=15)
    GAP_THRESHOLD = timedelta(minutes=30)  # > 30 min = gap in M15 data

    def __init__(self):
        self.logger = setup_logger()

    def clean(self, raw_candles: list) -> list:
        """
        Full cleaning pipeline.

        Args:
            raw_candles: Raw list of candle dicts

        Returns:
            Cleaned list of candle dicts
        """
        self.logger.info(f"Cleaning {len(raw_candles)} raw candles")

        candles = self._deduplicate(raw_candles)
        candles = self._remove_invalid(candles)
        candles = self._remove_gaps(candles)

        self.logger.info(
            f"Cleaning complete: {len(raw_candles)} → {len(candles)} candles "
            f"({len(raw_candles) - len(candles)} removed)"
        )
        return candles

    def _deduplicate(self, candles: list) -> list:
        """Remove candles with duplicate timestamps."""
        seen = set()
        unique = []
        for candle in candles:
            ts = candle["time"]
            if ts not in seen:
                seen.add(ts)
                unique.append(candle)
        return unique

    def _remove_invalid(self, candles: list) -> list:
        """Remove flat candles (high == low indicates no price movement)."""
        valid = []
        for candle in candles:
            mid = candle.get("mid", {})
            high = float(mid.get("h", 0))
            low = float(mid.get("l", 0))

            # Skip flat candles only
            if high == low:
                continue

            valid.append(candle)
        return valid

    def _remove_gaps(self, candles: list) -> list:
        """
        Remove candles that follow a gap > GAP_THRESHOLD.
        Keeps continuous segments only.
        """
        if len(candles) < 2:
            return candles

        continuous = [candles[0]]  # always keep first candle
        gaps_found = 0

        for i in range(1, len(candles)):
            prev_time = datetime.fromisoformat(
                candles[i-1]["time"].replace("Z", "+00:00")
            )
            curr_time = datetime.fromisoformat(
                candles[i]["time"].replace("Z", "+00:00")
            )
            gap = curr_time - prev_time

            if gap <= self.GAP_THRESHOLD:
                continuous.append(candles[i])
            else:
                gaps_found += 1
                self.logger.warning(
                    f"Gap removed at {candles[i]['time']}: {gap}"
                )

        self.logger.info(f"Gaps removed: {gaps_found}")
        return continuous
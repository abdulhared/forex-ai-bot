# training/data/historical_fetcher.py

import time
from datetime import datetime, timezone
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from app.shared.config import OANDA_API_KEY, OANDA_ENVIRONMENT
from app.infrastructure.monitoring.logger import setup_logger


class HistoricalFetcher:
    """
    Downloads historical OANDA candles for training.
    Paginates backwards in time, 5000 candles per request.
    """

    MAX_PER_REQUEST = 5000
    RATE_LIMIT_DELAY = 0.5  # seconds between requests

    def __init__(self):
        self.client = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.logger = setup_logger()

    def fetch(self, pair: str, granularity: str = "M15",
              target_candles: int = 70_000) -> list:
        """
        Fetch historical candles working backwards from now.

        Args:
            pair:            Instrument e.g. "EUR_USD"
            granularity:     Timeframe e.g. "M15"
            target_candles:  How many candles to collect

        Returns:
            List of candle dicts, oldest first
        """
        all_candles = []
        to_time = datetime.now(timezone.utc)  # start from now

        self.logger.info(f"Fetching {target_candles} {granularity} candles for {pair}")

        while len(all_candles) < target_candles:

            # Build request params
            params = {
                "granularity": granularity,
                "count": self.MAX_PER_REQUEST,
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            # Make request
            request = instruments.InstrumentsCandles(pair, params=params)
            response = self.client.request(request)
            candles = response["candles"]

            # Stop if no data returned
            if not candles:
                self.logger.info("No more candles available — stopping")
                break

            # Prepend chunk (we're going backwards — older data goes to front)
            all_candles = candles + all_candles

            # Update to_time — move to oldest candle in this chunk
            oldest_time_str = candles[0]["time"]  # index 0 = oldest
            to_time = datetime.fromisoformat(
                oldest_time_str.replace("Z", "+00:00")
            )

            self.logger.info(
                f"Fetched {len(candles)} candles | "
                f"Total: {len(all_candles)} | "
                f"Oldest: {oldest_time_str}"
            )

            # Respect rate limit
            time.sleep(self.RATE_LIMIT_DELAY)

        self.logger.info(f"Done. Total candles fetched: {len(all_candles)}")
        return all_candles
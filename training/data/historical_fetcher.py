# training/data/historical_fetcher.py

import pandas as pd
from typing import List, Dict, Any


class HistoricalFetcher:
    """Fetch and aggregate historical Forex data from Histdata.com CSV files."""
    
    def fetch(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Read M1 CSV, aggregate to M15, return candle dicts.
        
        Args:
            filepath: Path to Histdata.com CSV file (semicolon-separated, no header)
            
        Returns:
            List of candle dicts oldest first, formatted for data_cleaner.py
        """
        # Read CSV with semicolon separator, no header
        df = pd.read_csv(
            filepath, 
            sep=";", 
            header=None,
            names=["datetime", "open", "high", "low", "close", "volume"]
        )
        
        # Parse datetime and set as index
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
        df = df.set_index("datetime")
        
        # Resample to 15min with OHLCV aggregation rules
        m15 = df.resample("15min").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        
        # Convert to list of candle dicts with native Python types
        candles = []
        for timestamp, row in m15.iterrows():
            candle = {
                "time": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mid": {
                    "o": float(round(row["open"], 5)),
                    "h": float(round(row["high"], 5)),
                    "l": float(round(row["low"], 5)),
                    "c": float(round(row["close"], 5)),
                },
                "volume": int(row["volume"])
            }
            candles.append(candle)
        
        return candles
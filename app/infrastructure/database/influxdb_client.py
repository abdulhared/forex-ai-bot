from influxdb_client import InfluxDBClient as InfluxDBClientLib
from influxdb_client.client.write_api import SYNCHRONOUS
from app.shared.config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET


class InfluxClient:
    """
    InfluxDB client for storing and querying time-series candle data.
    Uses tags for low-cardinality data (pair, timeframe) and fields for 
    high-cardinality numeric data (OHLCV values).
    """
    
    def __init__(self):
        """
        Initialize InfluxDB client using configuration values.
        """
        self.client = InfluxDBClientLib(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.bucket = INFLUXDB_BUCKET
        self.org = INFLUXDB_ORG
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
    
    def write_candle(self, pair, timeframe, ohlcv):
        """
        Write a single candle to InfluxDB.
        
        Args:
            pair (str): Currency pair (e.g., "EUR_USD") - stored as tag
            timeframe (str): Timeframe (e.g., "1m", "5m", "1h") - stored as tag
            ohlcv (dict): Dictionary with keys open, high, low, close, volume - stored as fields
        """
        from influxdb_client import Point
        
        # Create a point with proper tag/field separation
        point = Point("candle") \
            .tag("pair", pair) \
            .tag("timeframe", timeframe) \
            .field("open", ohlcv["open"]) \
            .field("high", ohlcv["high"]) \
            .field("low", ohlcv["low"]) \
            .field("close", ohlcv["close"]) \
            .field("volume", ohlcv["volume"])
        
        # Write the point to the bucket
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
    
    def query_range(self, pair, timeframe, start, stop):
        """
        Query candles for a specific pair and timeframe within a time range.
        
        Args:
            pair (str): Currency pair to filter by
            timeframe (str): Timeframe to filter by
            start (str): Start timestamp (e.g., "2026-03-01T00:00:00Z")
            stop (str): Stop timestamp (e.g., "2026-03-28T00:00:00Z")
        
        Returns:
            List: Query results containing candle data
        """
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start}, stop: {stop})
          |> filter(fn: (r) => r._measurement == "candle")
          |> filter(fn: (r) => r.pair == "{pair}")
          |> filter(fn: (r) => r.timeframe == "{timeframe}")
        '''
        
        return self.query_api.query(query)
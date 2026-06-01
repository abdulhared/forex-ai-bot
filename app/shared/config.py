import os
from dotenv import load_dotenv

load_dotenv()

# ── Trading Pairs ─────────────────────────────────────────
TRADING_PAIRS = [
    "EUR_USD",
    "GBP_USD",
    "USD_JPY",
    "AUD_USD",
]

# ── Timeframes ────────────────────────────────────────────
TIMEFRAMES = ["M1", "M15", "H1", "H4"]
PRIMARY_TIMEFRAME = "M15"

# ── Risk Parameters ───────────────────────────────────────
MAX_RISK_PER_TRADE       = 0.01   # 1% of account balance
MAX_CONCURRENT_POSITIONS = 3
DAILY_LOSS_LIMIT         = 0.05   # 5% of opening balance
MAX_DRAWDOWN_LIMIT       = 0.10   # 10% from peak — triggers circuit breaker
MIN_MODEL_CONFIDENCE     = 0.65   # Minimum confidence to accept a signal
NEWS_BUFFER_MINUTES      = 15     # Minutes before/after news to block trading

# ── OANDA Broker ──────────────────────────────────────────
OANDA_API_KEY     = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID  = os.getenv("OANDA_ACCOUNT_ID")
OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")

# ── InfluxDB ──────────────────────────────────────────────
INFLUXDB_URL    = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN  = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG    = os.getenv("INFLUXDB_ORG", "forex-bot")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "market-data")

# ── Redis ─────────────────────────────────────────────────
REDIS_HOST     = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT     = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# ── API Security ──────────────────────────────────────────
API_KEY     = os.getenv("API_KEY")
API_KEY_DEV = os.getenv("API_KEY_DEV")

# ── Monitoring ────────────────────────────────────────────
SENTRY_DSN              = os.getenv("SENTRY_DSN")
TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID")
TRADINGVIEW_WEBHOOK_URL = os.getenv("TRADINGVIEW_WEBHOOK_URL")

# ── Application ───────────────────────────────────────────
APP_ENV   = os.getenv("APP_ENV", "development")
APP_HOST  = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT  = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Rolling Window ────────────────────────────────────────
ROLLING_WINDOW_SIZE = 200   # Candles kept in memory per pair per timeframe
LOOKBACK_WINDOW     = 50    # Candles the AI model looks back at per signal
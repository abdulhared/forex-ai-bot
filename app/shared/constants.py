from enum import Enum


class TradeAction(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingSession(str, Enum):
    SYDNEY   = "SYDNEY"
    TOKYO    = "TOKYO"
    LONDON   = "LONDON"
    NEW_YORK = "NEW_YORK"


class TimeFrame(str, Enum):
    M1  = "M1"
    M15 = "M15"
    H1  = "H1"
    H4  = "H4"


class Environment(str, Enum):
    PRACTICE = "practice"
    LIVE     = "live"


class LogCategory(str, Enum):
    TRADE       = "trade"
    SIGNAL      = "signal"
    ERROR       = "error"
    PERFORMANCE = "performance"
    SYSTEM      = "system"
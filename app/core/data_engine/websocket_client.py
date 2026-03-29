import oandapyV20
from oandapyV20.endpoints.pricing import PricingStream
import asyncio
from app.shared.config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_ENVIRONMENT, TRADING_PAIRS
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class WebSocketClient:
    """OANDA streaming price client with auto-reconnection"""
    
    def __init__(self):
        self.logger = setup_logger()
        
        # OANDA API client
        self.api = oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENVIRONMENT
        )
        self.account_id = OANDA_ACCOUNT_ID
        self.pairs = TRADING_PAIRS
        
        self.running = False  # Controls the main loop
        self.on_tick = None   # Callback for tick processing (inversion of control)
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"WebSocketClient initialized for pairs: {self.pairs}"
        )
    
    async def connect(self):
        """Connect to OANDA stream with exponential backoff on failure"""
        self.running = True  # Start the connection loop
        retry_count = 0
        max_retry_delay = 30
        
        while self.running:
            try:
                # Request stream for all trading pairs
                params = {"instruments": ",".join(self.pairs)}
                stream = PricingStream(
                    accountID=self.account_id,
                    params=params
                )
                
                self.logger.bind(category=LogCategory.SYSTEM.value).info(
                    f"Connecting to OANDA price stream..."
                )
                
                # Blocking iterator that yields each tick
                for tick in self.api.request(stream):
                    if not self.running:
                        break
                    
                    # Notify subscriber (candle aggregator, risk manager, etc.)
                    if self.on_tick:
                        self.on_tick(tick)
                    
                    retry_count = 0  # Reset counter on success
                    
            except Exception as e:
                retry_count += 1
                delay = min(2 ** retry_count, max_retry_delay)  # 2s, 4s, 8s, 16s, 30s
                
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"WebSocket connection failed (attempt {retry_count}): {e}. "
                    f"Reconnecting in {delay}s..."
                )
                
                await asyncio.sleep(delay)
    
    def disconnect(self):
        """Stop the streaming connection gracefully"""
        self.running = False
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            "WebSocket client disconnecting..."
        )
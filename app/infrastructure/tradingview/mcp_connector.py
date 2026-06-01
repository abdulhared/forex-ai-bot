# app/core/inference_engine/mcp_connector.py

import requests
from typing import Dict, Optional
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import TRADINGVIEW_WEBHOOK_URL


class TradingViewConnector:
    """
    Sends trade signals and explanations to TradingView in real time.
    Display only - never blocks or crashes the system if TradingView is unavailable.
    All publishing methods are wrapped in try/except and never raise exceptions.
    """
    
    def __init__(self, telegram_bot=None, webhook_url: str = None):
        """
        Initialize TradingView connector.
        
        Args:
            telegram_bot: Optional TelegramBot instance for sending failure alerts
            webhook_url: TradingView webhook URL from .env file (load via app.shared.config)
        """
        self.logger = setup_logger()
        self.telegram_bot = telegram_bot
        
        # Load webhook URL from config if not provided
        if webhook_url is None:
            webhook_url = TRADINGVIEW_WEBHOOK_URL
        
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        
        if self.enabled:
            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"TradingViewConnector enabled with webhook: {webhook_url[:50]}..."
            )
        else:
            self.logger.bind(category=LogCategory.SYSTEM.value).warning(
                "TradingViewConnector disabled: No webhook URL configured"
            )
    
    def _send_webhook(self, payload: Dict, event_type: str) -> bool:
        """
        Internal method to send webhook request with error handling.
        
        Args:
            payload: Dictionary to send as JSON
            event_type: String describing event type for logging (e.g., "signal", "trade_opened")
            
        Returns:
            True if request succeeded, False otherwise
        """
        if not self.enabled:
            self.logger.bind(category=LogCategory.SYSTEM.value).debug(
                f"Skipping {event_type} webhook: Connector disabled"
            )
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5  # 5 second timeout to avoid blocking
            )
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            
            self.logger.bind(category=LogCategory.SYSTEM.value).debug(
                f"Webhook {event_type} sent successfully: {response.status_code}"
            )
            return True
            
        except requests.exceptions.Timeout:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Webhook {event_type} timeout after 5 seconds"
            )
            self._notify_failure(f"Timeout sending {event_type} to TradingView")
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Webhook {event_type} connection error: {e}"
            )
            self._notify_failure(f"Connection error sending {event_type} to TradingView: {e}")
            return False
            
        except requests.exceptions.RequestException as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Webhook {event_type} request failed: {e}"
            )
            self._notify_failure(f"Failed to send {event_type} to TradingView: {e}")
            return False
            
        except Exception as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Webhook {event_type} unexpected error: {e}"
            )
            self._notify_failure(f"Unexpected error sending {event_type}: {e}")
            return False
    
    def _notify_failure(self, message: str):
        """Send failure notification via Telegram if bot is available."""
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(
                    f"⚠️ TradingView Connector Issue\n\n{message}\n\n"
                    f"Trading continues normally, but signals won't appear on charts."
                )
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram failure alert: {e}"
                )
    
    def publish_signal(self, signal: Dict, explanation: Dict) -> bool:
        """
        Publish signal explanation to TradingView.
        
        Args:
            signal: Dict from signal_generator.py containing:
                - pair, action, confidence, stop_loss, take_profit
                - risk_reward, lot_size, model_version, timestamp
            explanation: Dict from signal_explainer.py containing:
                - pair, action, confidence, confluence_score
                - risk_reward, reasons, recommendation, timestamp
                
        Returns:
            True on success, False on failure (never raises exception)
        """
        # Build payload using required keys
        payload = {
            "event": "signal",
            "pair": signal["pair"],
            "action": signal["action"],
            "confidence": signal["confidence"],
            "stop_loss": signal.get("stop_loss"),
            "take_profit": signal.get("take_profit"),
            "risk_reward": explanation.get("risk_reward", signal.get("risk_reward")),
            "confluence_score": explanation.get("confluence_score"),
            "recommendation": explanation.get("recommendation"),
            "timestamp": explanation.get("timestamp", signal.get("timestamp")),
            "model_version": signal.get("model_version")
        }
        
        # Add top reasons for quick reference (limit to 3)
        reasons = explanation.get("reasons", [])
        if reasons:
            payload["top_reasons"] = [
                {"factor": r["factor"], "score": r["score"]} 
                for r in reasons[:3]
            ]
        
        # Send webhook
        return self._send_webhook(payload, "signal")
    
    def publish_trade_opened(self, signal: Dict, trade_id: str, entry_price: float) -> bool:
        """
        Publish trade entry to TradingView.
        
        Args:
            signal: Dict from signal_generator.py containing:
                - pair, action, confidence, stop_loss, take_profit, risk_reward
            trade_id: Trade ID from order_placer.py or paper_trader.py response
            entry_price: Actual fill price (after slippage)
            
        Returns:
            True on success, False on failure (never raises exception)
        """
        # Build payload
        payload = {
            "event": "trade_opened",
            "trade_id": trade_id,
            "pair": signal["pair"],
            "action": signal["action"],
            "entry_price": entry_price,
            "stop_loss": signal.get("stop_loss"),
            "take_profit": signal.get("take_profit"),
            "risk_reward": signal.get("risk_reward"),
            "confidence": signal.get("confidence"),
            "timestamp": signal.get("timestamp")
        }
        
        # Send webhook
        return self._send_webhook(payload, "trade_opened")
    
    def publish_trade_closed(
        self,
        trade_id: str,
        pair: str,
        action: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_pips: float
    ) -> bool:
        """
        Publish trade exit to TradingView.
        
        Args:
            trade_id: Trade ID from order_placer.py or paper_trader.py
            pair: Instrument pair (e.g., "EUR_USD")
            action: Trade direction ("BUY" or "SELL")
            entry_price: Entry price of the trade
            exit_price: Exit price of the trade
            pnl: Profit/Loss in monetary value (matches paper_trader.py close_position)
            pnl_pips: Profit/Loss in pips (matches paper_trader.py close_position)
            
        Returns:
            True on success, False on failure (never raises exception)
        """
        # Calculate return percentage
        # For standard lots, rough approximation of return
        try:
            # If entry_price > 0, calculate percentage return
            price_change_pct = abs((exit_price - entry_price) / entry_price) * 100
            if pnl > 0:
                return_pct = price_change_pct
            else:
                return_pct = -price_change_pct
        except (ZeroDivisionError, TypeError):
            return_pct = 0
        
        # Build payload
        payload = {
            "event": "trade_closed",
            "trade_id": trade_id,
            "pair": pair,
            "action": action,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": round(pnl, 2),
            "pnl_pips": round(pnl_pips, 1),
            "return_pct": round(return_pct, 2),
            "timestamp": None  # Will be filled by TradingView webhook receiver
        }
        
        # Send webhook
        return self._send_webhook(payload, "trade_closed")
    
    def publish_bulk_trades(self, trades: list) -> dict:
        """
        Publish multiple closed trades to TradingView (for backtest results).
        
        Args:
            trades: List of trade dicts from backtester.py or paper_trader.py
                   Each trade should have: pair, action, entry_price, exit_price,
                   pnl, pnl_pips (optional)
            
        Returns:
            Dict with success count and failure count
        """
        if not self.enabled:
            return {"success": 0, "failed": 0, "message": "Connector disabled"}
        
        success_count = 0
        failure_count = 0
        
        for trade in trades:
            result = self.publish_trade_closed(
                trade_id=trade.get("trade_id", f"BULK_{trade.get('entry_step', 'unknown')}"),
                pair=trade.get("pair", "EUR_USD"),
                action=trade.get("action", "BUY"),
                entry_price=trade.get("entry_price", 0),
                exit_price=trade.get("exit_price", 0),
                pnl=trade.get("pnl", 0),
                pnl_pips=trade.get("pnl_pips", 0)
            )
            
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"Bulk publish completed: {success_count} succeeded, {failure_count} failed"
        )
        
        return {
            "success": success_count,
            "failed": failure_count,
            "total": len(trades)
        }
    
    def is_enabled(self) -> bool:
        """
        Check if TradingView connector is enabled.
        
        Returns:
            True if webhook URL is configured and connector can publish
        """
        return self.enabled
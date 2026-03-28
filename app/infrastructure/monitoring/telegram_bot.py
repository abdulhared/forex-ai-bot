import httpx
from app.shared.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class TelegramBot:
    """
    Telegram bot client for sending notifications about trades, alerts, and system events.
    Uses HTML formatting for better readability and visual hierarchy.
    """
    
    def __init__(self):
        """
        Initialize Telegram bot with token and chat ID from config.
        Logs warning if credentials are missing.
        """
        self.logger = setup_logger()
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Check if credentials are configured
        if not self.token or not self.chat_id:
            self.logger.bind(category=LogCategory.SYSTEM.value).warning(
                "Telegram bot not configured — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. "
                "Telegram notifications will be disabled."
            )
            self.enabled = False
        else:
            self.enabled = True
            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                "Telegram bot initialized — notifications enabled"
            )
    
    def send_message(self, message):
        """
        Send a message via Telegram API.
        
        Args:
            message (str): Message text with optional HTML formatting
        """
        if not self.enabled:
            return
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                # Log successful send (optional — could be noisy in production)
                self.logger.bind(category=LogCategory.SYSTEM.value).debug(
                    f"Telegram message sent successfully"
                )
        
        except httpx.HTTPError as e:
            # Safely check if response exists before accessing it
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                error_detail = f" — Response: {e.response.text}"
            
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Failed to send Telegram message: {e}{error_detail}"
            )
        except Exception as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Unexpected error sending Telegram message: {e}"
            )
    
    def send_trade_opened(self, trade_data):
        """
        Send notification when a trade is opened.
        
        Args:
            trade_data (dict): Trade dictionary with id, pair, action, lot_size, entry_price, stop_loss, take_profit
        """
        message = f"""🟢 <b>Trade Opened</b>
ID: <code>{trade_data['id'][:8]}...</code>
Pair: {trade_data['pair']}
Action: {trade_data['action']}
Lot Size: {trade_data['lot_size']}
Entry: {trade_data['entry_price']}
SL: {trade_data['stop_loss']} | TP: {trade_data['take_profit']}"""
        
        self.send_message(message)
    
    def send_trade_closed(self, trade_data, pnl):
        """
        Send notification when a trade is closed with profit/loss.
        
        Args:
            trade_data (dict): Trade dictionary with id, pair, action, lot_size, entry_price, close_price
            pnl (float): Profit or loss amount
        """
        pnl_symbol = "🟢" if pnl >= 0 else "🔴"
        pnl_formatted = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        
        message = f"""{pnl_symbol} <b>Trade Closed</b>
ID: <code>{trade_data['id'][:8]}...</code>
Pair: {trade_data['pair']}
Action: {trade_data['action']}
Lot Size: {trade_data['lot_size']}
Entry: {trade_data['entry_price']}
Close: {trade_data.get('close_price', 'N/A')}
PnL: <b>{pnl_formatted}</b>"""
        
        self.send_message(message)
    
    def send_alert(self, message):
        """
        Send a generic alert (circuit breaker, daily halt, etc.).
        
        Args:
            message (str): Alert message
        """
        formatted_message = f"⚠️ <b>ALERT</b>\n{message}"
        self.send_message(formatted_message)
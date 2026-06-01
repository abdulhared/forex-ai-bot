# app/core/risk_engine/prop_firm.py

from typing import Dict, Optional
from datetime import datetime
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class PropFirmManager:
    """
    Enforces prop firm challenge rules before any trade is placed.
    Sits between risk manager and execution engine.
    Both order_placer.py and paper_trader.py must pass through this check.
    """
    
    def __init__(self, firm_type: str = "FTMO", telegram_bot=None):
        """
        Initialize prop firm manager.
        
        Args:
            firm_type: Type of prop firm ("FTMO", "TOPSTEP", "MYFOREXFUNDS")
            telegram_bot: Optional TelegramBot instance for sending alerts
        """
        self.logger = setup_logger()
        self.telegram_bot = telegram_bot
        self.firm_type = firm_type
        
        # Define rules for each prop firm
        self.rules = {
            "FTMO": {
                "daily_loss_limit": 0.05,      # 5% daily loss limit
                "max_drawdown": 0.10,          # 10% max drawdown from peak
                "profit_target": 0.10,         # 10% profit target
                "trading_days": 30,            # 30 trading days to complete
                "news_blackout_minutes": 60    # 60 minutes before/after news
            },
            "TOPSTEP": {
                "daily_loss_limit": 0.05,      # 5% daily loss limit
                "max_drawdown": 0.12,          # 12% max drawdown from peak
                "profit_target": 0.06,         # 6% profit target
                "trading_days": 30,            # 30 trading days to complete
                "news_blackout_minutes": 30    # 30 minutes before/after news
            },
            "MYFOREXFUNDS": {
                "daily_loss_limit": 0.05,      # 5% daily loss limit
                "max_drawdown": 0.12,          # 12% max drawdown from peak
                "profit_target": 0.08,         # 8% profit target
                "trading_days": 30,            # 30 trading days to complete
                "news_blackout_minutes": 45    # 45 minutes before/after news
            }
        }
        
        # Validate firm_type
        if firm_type not in self.rules:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Unknown firm_type: {firm_type}. Must be one of {list(self.rules.keys())}"
            )
            raise ValueError(f"Invalid firm_type: {firm_type}")
        
        # Daily tracking variables
        self.daily_pnl: float = 0.0
        self.peak_balance: Optional[float] = None
        self.initial_balance: Optional[float] = None
        self.current_balance: Optional[float] = None
        self.trading_day: Optional[str] = None
        self.daily_start_balance: Optional[float] = None
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"PropFirmManager initialized for {firm_type} with rules: "
            f"daily_loss_limit={self.rules[firm_type]['daily_loss_limit']:.0%}, "
            f"max_drawdown={self.rules[firm_type]['max_drawdown']:.0%}, "
            f"profit_target={self.rules[firm_type]['profit_target']:.0%}"
        )
    
    def setup(self, initial_balance: float, date: str) -> None:
        """
        Called once at the start of a challenge.
        
        Args:
            initial_balance: Starting account balance
            date: Current date (YYYY-MM-DD string)
        """
        self.initial_balance = initial_balance
        self.peak_balance = initial_balance
        self.current_balance = initial_balance
        self.trading_day = date
        self.daily_start_balance = initial_balance
        self.daily_pnl = 0.0
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"PropFirm challenge setup complete: initial_balance=${initial_balance:.2f}, "
            f"trading_day={date}, firm={self.firm_type}"
        )
        
        # Send Telegram notification
        if self.telegram_bot:
            try:
                rules = self.rules[self.firm_type]
                message = (
                    f"🏆 PROP FIRM CHALLENGE STARTED\n\n"
                    f"Firm: {self.firm_type}\n"
                    f"Initial Balance: ${initial_balance:,.2f}\n"
                    f"Daily Loss Limit: {rules['daily_loss_limit']:.0%}\n"
                    f"Max Drawdown: {rules['max_drawdown']:.0%}\n"
                    f"Profit Target: {rules['profit_target']:.0%}\n"
                    f"Trading Days: {rules['trading_days']}\n"
                    f"News Blackout: {rules['news_blackout_minutes']} min\n\n"
                    f"Good luck! 🍀"
                )
                self.telegram_bot.send_message(message)
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram setup alert: {e}"
                )
    
    def update_balance(self, current_balance: float, date: str) -> None:
        """
        Called after every trade closes.
        
        Args:
            current_balance: Current account balance
            date: Current date (YYYY-MM-DD string)
        """
        if self.initial_balance is None:
            self.logger.bind(category=LogCategory.WARNING.value).warning(
                "update_balance called before setup(). Call setup() first."
            )
            return
        
        # Check if it's a new trading day
        if date != self.trading_day:
            # Reset daily tracking for new day
            self.daily_pnl = 0.0
            self.daily_start_balance = current_balance
            self.trading_day = date
            
            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"New trading day {date}: starting balance=${current_balance:.2f}"
            )
        else:
            # Calculate daily PnL for the current day
            if self.daily_start_balance is not None:
                self.daily_pnl = current_balance - self.daily_start_balance
        
        # Update current balance
        self.current_balance = current_balance
        
        # Update peak balance if current exceeds peak
        if self.peak_balance is not None and current_balance > self.peak_balance:
            self.peak_balance = current_balance
            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"New peak balance: ${self.peak_balance:.2f}"
            )
        
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"Balance updated: current=${current_balance:.2f}, "
            f"peak=${self.peak_balance:.2f}, daily_pnl=${self.daily_pnl:.2f}"
        )
    
    def check_compliance(self, signal: Dict) -> Dict:
        """
        Check if a trade complies with prop firm rules.
        
        Args:
            signal: Dict from signal_generator.py containing:
                - pair, action, confidence, stop_loss, take_profit
                - risk_reward, lot_size, model_version, timestamp
                
        Returns:
            Dict with keys:
                - allowed: bool
                - reason: str
                - firm_type: str
                - daily_loss_pct: float
                - drawdown_pct: float
                - rules: dict
        """
        # Check if setup was called
        if self.initial_balance is None:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                "check_compliance called before setup(). Call setup() first."
            )
            return {
                "allowed": False,
                "reason": "PropFirmManager not initialized. Call setup() first.",
                "firm_type": self.firm_type,
                "daily_loss_pct": 0.0,
                "drawdown_pct": 0.0,
                "rules": self.rules[self.firm_type]
            }
        
        # Get rules for current firm
        rules = self.rules[self.firm_type]
        
        # Calculate daily loss percentage
        if self.initial_balance > 0:
            daily_loss_pct = -self.daily_pnl / self.initial_balance if self.daily_pnl < 0 else 0.0
        else:
            daily_loss_pct = 0.0
        
        # Check 1: Daily loss limit
        if daily_loss_pct >= rules["daily_loss_limit"]:
            reason = (
                f"Daily loss limit exceeded: {daily_loss_pct:.2%} >= {rules['daily_loss_limit']:.0%}. "
                f"Daily PnL: ${self.daily_pnl:.2f}"
            )
            
            self.logger.bind(category=LogCategory.ERROR.value).error(reason)
            
            # Send Telegram alert
            if self.telegram_bot:
                try:
                    message = (
                        f"⚠️ PROP FIRM VIOLATION ⚠️\n\n"
                        f"Firm: {self.firm_type}\n"
                        f"Rule: Daily Loss Limit\n"
                        f"Limit: {rules['daily_loss_limit']:.0%}\n"
                        f"Current Loss: {daily_loss_pct:.2%}\n"
                        f"Daily PnL: ${self.daily_pnl:.2f}\n"
                        f"Balance: ${self.current_balance:,.2f}\n\n"
                        f"Trading blocked for rest of day."
                    )
                    self.telegram_bot.send_message(message)
                except Exception as e:
                    self.logger.bind(category=LogCategory.ERROR.value).error(
                        f"Failed to send Telegram violation alert: {e}"
                    )
            
            return {
                "allowed": False,
                "reason": reason,
                "firm_type": self.firm_type,
                "daily_loss_pct": round(daily_loss_pct, 4),
                "drawdown_pct": 0.0,
                "rules": rules
            }
        
        # Calculate drawdown from peak
        if self.peak_balance is not None and self.peak_balance > 0:
            drawdown_pct = (self.peak_balance - self.current_balance) / self.peak_balance
        else:
            drawdown_pct = 0.0
        
        # Check 2: Max drawdown limit
        if drawdown_pct >= rules["max_drawdown"]:
            reason = (
                f"Max drawdown limit exceeded: {drawdown_pct:.2%} >= {rules['max_drawdown']:.0%}. "
                f"Peak: ${self.peak_balance:.2f}, Current: ${self.current_balance:.2f}"
            )
            
            self.logger.bind(category=LogCategory.ERROR.value).error(reason)
            
            # Send Telegram alert
            if self.telegram_bot:
                try:
                    message = (
                        f"⚠️ PROP FIRM VIOLATION ⚠️\n\n"
                        f"Firm: {self.firm_type}\n"
                        f"Rule: Maximum Drawdown\n"
                        f"Limit: {rules['max_drawdown']:.0%}\n"
                        f"Current Drawdown: {drawdown_pct:.2%}\n"
                        f"Peak Balance: ${self.peak_balance:,.2f}\n"
                        f"Current Balance: ${self.current_balance:,.2f}\n"
                        f"Loss from Peak: ${self.peak_balance - self.current_balance:,.2f}\n\n"
                        f"Trading permanently blocked - Challenge failed."
                    )
                    self.telegram_bot.send_message(message)
                except Exception as e:
                    self.logger.bind(category=LogCategory.ERROR.value).error(
                        f"Failed to send Telegram violation alert: {e}"
                    )
            
            return {
                "allowed": False,
                "reason": reason,
                "firm_type": self.firm_type,
                "daily_loss_pct": round(daily_loss_pct, 4),
                "drawdown_pct": round(drawdown_pct, 4),
                "rules": rules
            }
        
        # Check 3: Profit target achieved (optional - just informational)
        profit_pct = (self.current_balance - self.initial_balance) / self.initial_balance if self.initial_balance > 0 else 0.0
        
        if profit_pct >= rules["profit_target"]:
            self.logger.bind(category=LogCategory.SYSTEM.value).info(
                f"Profit target achieved: {profit_pct:.2%} >= {rules['profit_target']:.0%}. "
                f"Challenge completed successfully!"
            )
            
            # Send Telegram alert for profit target
            if self.telegram_bot:
                try:
                    message = (
                        f"🏆 PROP FIRM CHALLENGE COMPLETED 🏆\n\n"
                        f"Firm: {self.firm_type}\n"
                        f"Profit Target: {rules['profit_target']:.0%}\n"
                        f"Achieved: {profit_pct:.2%}\n"
                        f"Final Balance: ${self.current_balance:,.2f}\n"
                        f"Total Profit: ${self.current_balance - self.initial_balance:,.2f}\n\n"
                        f"Congratulations! 🎉"
                    )
                    self.telegram_bot.send_message(message)
                except Exception as e:
                    self.logger.bind(category=LogCategory.ERROR.value).error(
                        f"Failed to send Telegram profit target alert: {e}"
                    )
        
        # All checks passed
        return {
            "allowed": True,
            "reason": "All compliance checks passed",
            "firm_type": self.firm_type,
            "daily_loss_pct": round(daily_loss_pct, 4),
            "drawdown_pct": round(drawdown_pct, 4),
            "rules": rules,
            "profit_pct": round(profit_pct, 4)
        }
    
    def get_status(self) -> Dict:
        """
        Get current challenge status.
        
        Returns:
            Dict with keys:
                - firm_type: str
                - daily_pnl: float
                - daily_loss_pct: float
                - drawdown_pct: float
                - peak_balance: float
                - current_balance: float
                - initial_balance: float
                - profit_pct: float
                - rules: dict
                - is_active: bool
                - trading_day: str
        """
        if self.initial_balance is None:
            return {
                "firm_type": self.firm_type,
                "is_active": False,
                "message": "Challenge not started. Call setup() first."
            }
        
        # Calculate percentages
        if self.initial_balance > 0:
            profit_pct = (self.current_balance - self.initial_balance) / self.initial_balance
        else:
            profit_pct = 0.0
        
        if self.initial_balance > 0:
            daily_loss_pct = -self.daily_pnl / self.initial_balance if self.daily_pnl < 0 else 0.0
        else:
            daily_loss_pct = 0.0
        
        if self.peak_balance is not None and self.peak_balance > 0:
            drawdown_pct = (self.peak_balance - self.current_balance) / self.peak_balance
        else:
            drawdown_pct = 0.0
        
        rules = self.rules[self.firm_type]
        
        # Check if challenge is still active
        is_active = True
        if drawdown_pct >= rules["max_drawdown"]:
            is_active = False
        elif daily_loss_pct >= rules["daily_loss_limit"]:
            is_active = True  # Still active, just blocked for the day
        
        return {
            "firm_type": self.firm_type,
            "is_active": is_active,
            "trading_day": self.trading_day,
            "initial_balance": round(self.initial_balance, 2),
            "current_balance": round(self.current_balance, 2),
            "peak_balance": round(self.peak_balance, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_loss_pct": round(daily_loss_pct, 4),
            "drawdown_pct": round(drawdown_pct, 4),
            "profit_pct": round(profit_pct, 4),
            "rules": rules,
            "profit_target_achieved": profit_pct >= rules["profit_target"],
            "daily_limit_reached": daily_loss_pct >= rules["daily_loss_limit"],
            "drawdown_limit_reached": drawdown_pct >= rules["max_drawdown"]
        }
    
    def get_daily_remaining_risk(self) -> float:
        """
        Calculate remaining risk available for the day.
        
        Returns:
            float: Remaining daily loss limit in dollars (negative if exceeded)
        """
        if self.initial_balance is None or self.daily_start_balance is None:
            return 0.0
        
        rules = self.rules[self.firm_type]
        max_daily_loss_amount = self.initial_balance * rules["daily_loss_limit"]
        current_loss_amount = -self.daily_pnl if self.daily_pnl < 0 else 0.0
        
        remaining_risk = max_daily_loss_amount - current_loss_amount
        return round(remaining_risk, 2)
    
    def reset_challenge(self, new_initial_balance: float, date: str) -> None:
        """
        Reset the challenge (for failed challenges or new attempts).
        
        Args:
            new_initial_balance: New starting balance
            date: Current date (YYYY-MM-DD string)
        """
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"Resetting prop firm challenge for {self.firm_type}. "
            f"Previous balance: ${self.current_balance:.2f} → New: ${new_initial_balance:.2f}"
        )
        
        # Send Telegram notification
        if self.telegram_bot:
            try:
                message = (
                    f"🔄 PROP FIRM CHALLENGE RESET\n\n"
                    f"Firm: {self.firm_type}\n"
                    f"Previous Balance: ${self.current_balance:,.2f}\n"
                    f"New Balance: ${new_initial_balance:,.2f}\n"
                    f"Starting fresh challenge."
                )
                self.telegram_bot.send_message(message)
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram reset alert: {e}"
                )
        
        # Reset all tracking variables
        self.setup(new_initial_balance, date)
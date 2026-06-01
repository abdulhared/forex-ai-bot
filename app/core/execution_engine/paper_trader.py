# app/core/execution_engine/paper_trader.py

import uuid
from typing import Dict, Optional, List
from datetime import datetime, timezone

from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class PaperTrader:
    """
    Simulates order execution without touching a real broker.
    Uses the same interface as order_placer.py so the rest of the system
    doesn't need to change when switching between paper and live trading.
    """
    
    def __init__(self, initial_balance: float = 10000.0, telegram_bot=None, spread_pips: float = 1.5):
        """
        Initialize paper trader.
        
        Args:
            initial_balance: Starting account balance (default: 10000)
            telegram_bot: Optional TelegramBot instance for sending alerts
            spread_pips: Spread cost in pips (default: 1.5)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.spread_pips = spread_pips
        self.pip_value = 0.10  # Standard for EUR/USD
        self.telegram_bot = telegram_bot
        
        # Track positions and trades
        self.open_positions: Dict[str, dict] = {}  # trade_id -> position dict
        self.closed_trades: List[dict] = []
        self.trade_counter = 0
        
        self.logger = setup_logger()
        
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"PaperTrader initialized with balance ${initial_balance:.2f}, spread={spread_pips} pips"
        )
        
        # Send Telegram notification if bot is configured
        if self.telegram_bot:
            try:
                self.telegram_bot.send_message(
                    f"📝 Paper Trading Mode Enabled\n"
                    f"Initial Balance: ${initial_balance:.2f}\n"
                    f"Spread: {spread_pips} pips\n"
                    f"Pip Value: ${self.pip_value}"
                )
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram initialization alert: {e}"
                )
    
    def place_order(self, signal: dict, lot_size: float, current_price: float) -> dict:
        """
        Place a simulated market order based on a signal.
        
        Args:
            signal: dict with keys — pair, action, stop_loss, take_profit, confidence
            lot_size: float (e.g. 0.02)
            current_price: Current market price from data engine (e.g., 1.07315)
            
        Returns:
            dict with success status and either response or error details
            Matches order_placer.py interface
        """
        # Guard: HOLD action should not place an order
        if signal["action"] == "HOLD":
            self.logger.info(
                f"Skipping paper order: Action is HOLD for {signal['pair']}"
            )
            return {
                "success": True,
                "skipped": True,
                "message": "Action was HOLD, no order placed"
            }
        
        # Generate trade ID
        self.trade_counter += 1
        trade_id = f"PAPER_{self.trade_counter}_{uuid.uuid4().hex[:8]}"
        
        # Convert lot size to units (negative for SELL)
        units = lot_size * 100000
        if signal["action"] == "SELL":
            units = -units
        
        # Simulate slippage of 0.5 pips on entry
        slippage_pips = 0.5
        slippage_price = slippage_pips * 0.0001  # Convert pips to price
        
        # Use the actual current_price passed from data engine
        if signal["action"] == "BUY":
            entry_price = current_price + slippage_price
        else:  # SELL
            entry_price = current_price - slippage_price
        
        # Round to 5 decimal places
        entry_price = round(entry_price, 5)
        
        # Store position
        position = {
            "trade_id": trade_id,
            "pair": signal["pair"],
            "action": signal["action"],
            "lot_size": lot_size,
            "units": units,
            "entry_price": entry_price,
            "entry_market_price": current_price,  # Store original market price for reference
            "slippage_pips": slippage_pips,
            "stop_loss": signal.get("stop_loss"),
            "take_profit": signal.get("take_profit"),
            "confidence": signal.get("confidence"),
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "status": "open"
        }
        
        self.open_positions[trade_id] = position
        
        # Log the trade
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"PAPER TRADE OPENED: {trade_id} | {signal['action']} {signal['pair']} | "
            f"Lot: {lot_size} | Market: {current_price:.5f} | Entry: {entry_price:.5f} | Units: {int(units)}"
        )
        
        # Send Telegram alert
        if self.telegram_bot:
            try:
                message = (
                    f"📈 PAPER TRADE OPENED\n"
                    f"ID: {trade_id}\n"
                    f"Pair: {signal['pair']}\n"
                    f"Action: {signal['action']}\n"
                    f"Lot Size: {lot_size}\n"
                    f"Market Price: {current_price:.5f}\n"
                    f"Entry Price: {entry_price:.5f}\n"
                    f"Slippage: {slippage_pips} pips\n"
                    f"Stop Loss: {signal.get('stop_loss', 'N/A')}\n"
                    f"Take Profit: {signal.get('take_profit', 'N/A')}\n"
                    f"Confidence: {signal.get('confidence', 0):.2%}"
                )
                self.telegram_bot.send_message(message)
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram open trade alert: {e}"
                )
        
        # Return same structure as order_placer.py
        return {
            "success": True,
            "response": {
                "orderCreate": {
                    "order": {
                        "id": trade_id,
                        "instrument": signal["pair"],
                        "units": str(int(units)),
                        "price": entry_price,
                        "type": "MARKET"
                    },
                    "orderFillTransaction": {
                        "id": trade_id,
                        "price": entry_price,
                        "units": str(int(units))
                    }
                }
            },
            "paper_trade": True,
            "trade_id": trade_id
        }
    
    def close_position(self, trade_id: str, current_price: float) -> dict:
        """
        Close a simulated open position at current price.
        
        Args:
            trade_id: ID of the position to close
            current_price: Current market price to close at
            
        Returns:
            dict with success status and PnL details
        """
        # Look up position
        if trade_id not in self.open_positions:
            error_msg = f"Trade {trade_id} not found in open positions"
            self.logger.bind(category=LogCategory.ERROR.value).error(error_msg)
            return {
                "success": False,
                "error_code": 404,
                "error_message": error_msg
            }
        
        position = self.open_positions[trade_id]
        
        # Simulate slippage of 0.5 pips on exit
        slippage_pips = 0.5
        slippage_price = slippage_pips * 0.0001
        
        if position["action"] == "BUY":
            exit_price = current_price - slippage_price
            # PnL in pips for BUY: (exit_price - entry_price) / 0.0001
            pnl_pips = (exit_price - position["entry_price"]) / 0.0001
        else:  # SELL
            exit_price = current_price + slippage_price
            # PnL in pips for SELL: (entry_price - exit_price) / 0.0001
            pnl_pips = (position["entry_price"] - exit_price) / 0.0001
        
        # Deduct spread on exit (spread cost is applied on both entry and exit)
        pnl_pips -= self.spread_pips
        
        # Round to 1 decimal place
        pnl_pips = round(pnl_pips, 1)
        
        # Convert to monetary value
        pnl_monetary = pnl_pips * self.pip_value
        
        # Update balance
        self.balance += pnl_monetary
        
        # Move to closed trades
        closed_trade = {
            **position,
            "exit_price": round(exit_price, 5),
            "exit_market_price": current_price,  # Store original market price for reference
            "exit_slippage_pips": slippage_pips,
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "pnl_pips": pnl_pips,
            "pnl": round(pnl_monetary, 2),
            "status": "closed",
            "balance_after": round(self.balance, 2)
        }
        
        self.closed_trades.append(closed_trade)
        del self.open_positions[trade_id]
        
        # Log the close
        self.logger.bind(category=LogCategory.SYSTEM.value).info(
            f"PAPER TRADE CLOSED: {trade_id} | {position['action']} {position['pair']} | "
            f"PnL: ${pnl_monetary:.2f} ({pnl_pips:+} pips) | Balance: ${self.balance:.2f}"
        )
        
        # Send Telegram alert
        if self.telegram_bot:
            try:
                message = (
                    f"📉 PAPER TRADE CLOSED\n"
                    f"ID: {trade_id}\n"
                    f"Pair: {position['pair']}\n"
                    f"Action: {position['action']}\n"
                    f"Entry: {position['entry_price']:.5f}\n"
                    f"Exit: {exit_price:.5f}\n"
                    f"Market Price: {current_price:.5f}\n"
                    f"PnL: ${pnl_monetary:.2f} ({pnl_pips:+} pips)\n"
                    f"Balance: ${self.balance:.2f}\n"
                    f"Return: {(pnl_monetary / (position['lot_size'] * 100000 * self.pip_value)):.2%}"
                )
                self.telegram_bot.send_message(message)
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram close trade alert: {e}"
                )
        
        return {
            "success": True,
            "trade_id": trade_id,
            "pnl_pips": pnl_pips,
            "pnl": round(pnl_monetary, 2),
            "balance": round(self.balance, 2),
            "response": closed_trade
        }
    
    def get_account_summary(self) -> dict:
        """
        Get current account summary.
        
        Returns:
            dict with:
                - balance: current account balance
                - open_positions_count: number of open positions
                - total_closed_trades: total number of closed trades
                - total_pnl: total profit/loss from all closed trades
                - win_rate: win rate percentage from closed trades
                - total_wins: number of winning trades
                - total_losses: number of losing trades
                - initial_balance: starting balance
                - total_return: total percentage return
        """
        # Calculate stats from closed trades
        total_pnl = sum(trade.get('pnl', 0) for trade in self.closed_trades)
        wins = [t for t in self.closed_trades if t.get('pnl', 0) > 0]
        losses = [t for t in self.closed_trades if t.get('pnl', 0) < 0]
        total_wins = len(wins)
        total_losses = len(losses)
        total_trades = len(self.closed_trades)
        
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0
        total_return = ((self.balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0.0
        
        return {
            "balance": round(self.balance, 2),
            "initial_balance": round(self.initial_balance, 2),
            "total_return": round(total_return, 2),
            "open_positions_count": len(self.open_positions),
            "total_closed_trades": total_trades,
            "total_pnl": round(total_pnl, 2),
            "total_wins": total_wins,
            "total_losses": total_losses,
            "win_rate": round(win_rate, 2),
            "avg_winner": round(sum(t.get('pnl', 0) for t in wins) / total_wins, 2) if total_wins > 0 else 0.0,
            "avg_loser": round(sum(t.get('pnl', 0) for t in losses) / total_losses, 2) if total_losses > 0 else 0.0
        }
    
    def get_open_positions(self) -> List[dict]:
        """
        Get all open positions.
        
        Returns:
            List of open position dicts
        """
        return list(self.open_positions.values())
    
    def get_closed_trades(self) -> List[dict]:
        """
        Get all closed trades.
        
        Returns:
            List of closed trade dicts
        """
        return self.closed_trades
    
    def reset(self) -> dict:
        """
        Reset everything back to initial state for a new paper trading session.
        
        Returns:
            dict with reset confirmation
        """
        # Store old stats for logging
        old_balance = self.balance
        old_total_trades = len(self.closed_trades)
        
        # Reset all state
        self.balance = self.initial_balance
        self.open_positions = {}
        self.closed_trades = []
        self.trade_counter = 0
        
        self.logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"PAPER TRADER RESET: Balance ${old_balance:.2f} → ${self.balance:.2f} | "
            f"Cleared {old_total_trades} trades"
        )
        
        # Send Telegram notification
        if self.telegram_bot:
            try:
                message = (
                    f"🔄 PAPER TRADER RESET\n"
                    f"Previous Balance: ${old_balance:.2f}\n"
                    f"Reset to: ${self.balance:.2f}\n"
                    f"Cleared {old_total_trades} trades\n"
                    f"Starting fresh paper trading session."
                )
                self.telegram_bot.send_message(message)
            except Exception as e:
                self.logger.bind(category=LogCategory.ERROR.value).error(
                    f"Failed to send Telegram reset alert: {e}"
                )
        
        return {
            "success": True,
            "message": "Paper trader reset to initial state",
            "reset_balance": self.balance,
            "cleared_trades": old_total_trades
        }
    
    def get_position_by_id(self, trade_id: str) -> Optional[dict]:
        """
        Get a specific open position by ID.
        
        Args:
            trade_id: Position ID to look up
            
        Returns:
            Position dict or None if not found
        """
        return self.open_positions.get(trade_id)
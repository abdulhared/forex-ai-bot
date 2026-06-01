# training/evaluation/metrics.py

import math
from typing import List, Dict


class Metrics:
    """
    Calculates performance statistics from a list of closed trades.
    Pure Python math, no external dependencies.
    """
    
    def calculate(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive performance metrics from closed trades.
        
        Args:
            trades: List of trade dictionaries, each containing:
                - pnl: float (profit/loss amount)
                - entry_price: float
                - exit_price: float
                - action: str ("BUY" or "SELL")
                - pair: str (optional)
                - entry_step: int (optional)
            
        Returns:
            Dictionary containing:
                - win_rate: float (0-1)
                - profit_factor: float (gross_profit / gross_loss, or inf if no losses)
                - max_drawdown: float (peak-to-trough decline as percentage)
                - total_pnl: float
                - average_winner: float
                - average_loser: float
                - sharpe_ratio: float (assuming risk-free rate = 0)
                - total_trades: int
                - consecutive_losses: int
        """
        if not trades:
            return self._empty_metrics()
        
        # Extract PnL values
        pnls = [trade['pnl'] for trade in trades]
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]
        
        # Basic counts
        total_trades = len(trades)
        wins = len(winning_pnls)
        losses = len(losing_pnls)
        
        # Win rate
        win_rate = wins / total_trades if total_trades > 0 else 0.0
        
        # Profit factor (gross_profit / gross_loss)
        gross_profit = sum(winning_pnls) if winning_pnls else 0.0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Total PnL
        total_pnl = sum(pnls)
        
        # Average winner and loser
        average_winner = gross_profit / wins if wins > 0 else 0.0
        average_loser = -gross_loss / losses if losses > 0 else 0.0
        
        # Maximum drawdown (peak-to-trough decline)
        max_drawdown = self._calculate_max_drawdown(pnls)
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe_ratio = self._calculate_sharpe_ratio(pnls)
        
        # Consecutive losses count
        consecutive_losses = self._calculate_consecutive_losses(pnls)
        
        return {
            'win_rate': round(win_rate, 4),
            'profit_factor': round(profit_factor, 4) if profit_factor != float('inf') else float('inf'),
            'max_drawdown': round(max_drawdown, 4),
            'total_pnl': round(total_pnl, 4),
            'average_winner': round(average_winner, 4),
            'average_loser': round(average_loser, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'total_trades': total_trades,
            'consecutive_losses': consecutive_losses,
            'wins': wins,
            'losses': losses,
            'gross_profit': round(gross_profit, 4),
            'gross_loss': round(gross_loss, 4)
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no trades available."""
        return {
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'total_pnl': 0.0,
            'average_winner': 0.0,
            'average_loser': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
            'consecutive_losses': 0,
            'wins': 0,
            'losses': 0,
            'gross_profit': 0.0,
            'gross_loss': 0.0
        }
    
    def _calculate_max_drawdown(self, pnls: List[float]) -> float:
        """
        Calculate maximum drawdown from a sequence of PnL values.
        Drawdown is measured as peak-to-trough decline as a percentage
        of the running total equity curve.
        """
        if not pnls:
            return 0.0
        
        # Calculate cumulative equity curve
        equity_curve = []
        running_total = 0.0
        for pnl in pnls:
            running_total += pnl
            equity_curve.append(running_total)
        
        # Find maximum drawdown
        peak = equity_curve[0]
        max_drawdown = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            if peak > 0:  # Avoid division by zero
                drawdown = (peak - equity) / abs(peak)
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, pnls: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio from PnL sequence.
        Assumes each trade represents one period and risk-free rate = 0 by default.
        """
        if len(pnls) < 2:
            return 0.0
        
        # Calculate mean and standard deviation of returns
        mean_return = sum(pnls) / len(pnls)
        
        variance = sum((p - mean_return) ** 2 for p in pnls) / len(pnls)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        # Sharpe ratio = (mean_return - risk_free_rate) / std_dev
        sharpe = (mean_return - risk_free_rate) / std_dev
        
        # Annualize if needed? Keeping as per-trade ratio for now
        return sharpe
    
    def _calculate_consecutive_losses(self, pnls: List[float]) -> int:
        """
        Calculate the maximum consecutive losing trades.
        """
        max_consecutive = 0
        current_consecutive = 0
        
        for pnl in pnls:
            if pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
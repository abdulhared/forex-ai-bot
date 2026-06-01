# training/evaluation/backtester.py

import numpy as np
import torch
from typing import List, Dict, Optional

# Import from existing modules for consistency with live trading
import sys
sys.path.append('.')

# These imports assume the paths exist in your project structure
try:
    from training.environment.reward_function import RewardFunction
    from app.core.inference_engine.signal_generator import ACTION_MAP
except ImportError:
    # Fallback definitions if imports fail
    ACTION_MAP = {0: "BUY", 1: "HOLD", 2: "SELL"}
    
    class RewardFunction:
        def __init__(self, spread_pips=1.5, pip_value=0.10, **kwargs):
            self.spread_pips = spread_pips
            self.pip_value = pip_value


class Backtester:
    """
    Simulates trading by walking through feature matrix step by step,
    calling the model for signals, and tracking open/closed positions.
    """
    
    def __init__(self, feature_matrix: np.ndarray, spread_pips: float = 1.5, pip_value: float = 0.10):
        """
        Initialize backtester with feature matrix.
        
        Args:
            feature_matrix: Numpy array of shape (n_steps, n_features)
                           First column (index 0) is assumed to be the close price
            spread_pips: Spread cost in pips
            pip_value: Value per pip in account currency
        """
        self.feature_matrix = feature_matrix
        self.spread_pips = spread_pips
        self.pip_value = pip_value
        self.reward_calc = RewardFunction(
            spread_pips=spread_pips,
            pip_value=pip_value
        )
        
    def run(self, model: torch.nn.Module) -> List[Dict]:
        """
        Run backtest by iterating through feature matrix.
        
        Args:
            model: Trained PyTorch model with forward() returning (action_probs, value)
            
        Returns:
            List of closed trade dictionaries, each containing:
                - pair: str (placeholder, e.g., "EUR_USD")
                - action: str ("BUY" or "SELL")
                - entry_price: float
                - exit_price: float
                - pnl: float (monetary value)
                - pnl_pips: float (profit/loss in pips)
                - entry_step: int
                - exit_step: int
        """
        closed_trades = []
        open_trade = None  # Will store: {'action', 'entry_price', 'entry_step', 'entry_index'}
        
        for step, features in enumerate(self.feature_matrix):
            # Extract actual price from feature matrix (first column = close price)
            current_price = features[0]
            
            # Skip first step if no previous price to compare
            if step == 0:
                continue
            
            # Convert features to tensor
            features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            
            # Get model prediction
            with torch.no_grad():
                action_probs, value = model(features_tensor)
                action_index = torch.argmax(action_probs, dim=1).item()
                confidence = action_probs[0][action_index].item()
            
            action = ACTION_MAP.get(action_index, "HOLD")
            
            # Minimum confidence threshold
            if confidence < 0.50:
                action = "HOLD"
            
            # Handle trade logic
            if open_trade is None:
                # No open position - can open if signal is BUY or SELL
                if action in ["BUY", "SELL"]:
                    # Deduct spread cost on entry (will be applied at exit)
                    spread_cost_pips = self.spread_pips
                    open_trade = {
                        'action': action,
                        'entry_price': current_price,
                        'entry_step': step,
                        'spread_cost_pips': spread_cost_pips
                    }
            else:
                # Have open position - check if we should close
                # Close on opposite signal or after maximum hold period
                should_close = False
                
                # Close on opposite signal
                if action != "HOLD" and action != open_trade['action']:
                    should_close = True
                
                # Also close after maximum hold period (e.g., 50 steps)
                if step - open_trade['entry_step'] >= 50:
                    should_close = True
                
                if should_close:
                    # Calculate PnL in pips using standard forex formula
                    if open_trade['action'] == "BUY":
                        pnl_pips = (current_price - open_trade['entry_price']) / 0.0001
                    else:  # SELL
                        pnl_pips = (open_trade['entry_price'] - current_price) / 0.0001
                    
                    # Deduct spread cost (in pips)
                    pnl_pips -= open_trade['spread_cost_pips']
                    
                    # Convert pips to monetary value
                    pnl_monetary = pnl_pips * self.pip_value
                    
                    # Create trade record
                    trade_record = {
                        'pair': "EUR_USD",  # Placeholder
                        'action': open_trade['action'],
                        'entry_price': round(open_trade['entry_price'], 5),
                        'exit_price': round(current_price, 5),
                        'pnl': round(pnl_monetary, 2),
                        'pnl_pips': round(pnl_pips, 1),
                        'entry_step': open_trade['entry_step'],
                        'exit_step': step,
                        'bars_held': step - open_trade['entry_step']
                    }
                    closed_trades.append(trade_record)
                    open_trade = None
        
        # Close any remaining open trade at the end
        if open_trade is not None:
            last_price = self.feature_matrix[-1][0]
            
            if open_trade['action'] == "BUY":
                pnl_pips = (last_price - open_trade['entry_price']) / 0.0001
            else:
                pnl_pips = (open_trade['entry_price'] - last_price) / 0.0001
            
            pnl_pips -= open_trade['spread_cost_pips']
            pnl_monetary = pnl_pips * self.pip_value
            
            trade_record = {
                'pair': "EUR_USD",
                'action': open_trade['action'],
                'entry_price': round(open_trade['entry_price'], 5),
                'exit_price': round(last_price, 5),
                'pnl': round(pnl_monetary, 2),
                'pnl_pips': round(pnl_pips, 1),
                'entry_step': open_trade['entry_step'],
                'exit_step': len(self.feature_matrix) - 1,
                'bars_held': len(self.feature_matrix) - 1 - open_trade['entry_step']
            }
            closed_trades.append(trade_record)
        
        return closed_trades
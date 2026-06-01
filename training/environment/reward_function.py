# training/environment/reward_function.py


class RewardFunction:
    """
    Calculates shaped reward signal for the PPO agent.
    Combines PnL reward with penalties to prevent reward hacking.
    """

    def __init__(
        self,
        spread_pips:       float = 1.5,   # typical EUR/USD spread
        hold_penalty:      float = 0.05,  # penalty per step in losing trade
        drawdown_penalty:  float = 5.0,   # multiplier for drawdown punishment
        profit_bonus:      float = 0.10,  # bonus for closing a profitable trade
        pip_value:         float = 0.10,
        overtrade_penalty:   float = 0.20,  # penalty for opening a new trade when already in one
        overtrade_window:    int = 20,      # number of recent steps to check for overtrading
        max_trades_in_window: int = 3,      # max trades allowed in the window
    ):
        self.spread_pips = spread_pips
        self.hold_penalty = hold_penalty
        self.drawdown_penalty = drawdown_penalty
        self.profit_bonus = profit_bonus
        self.pip_value = pip_value
        self.overtrade_penalty = overtrade_penalty
        self.overtrade_window = overtrade_window
        self.max_trades_in_window = max_trades_in_window
        
        # Track recent trades (sliding window)
        self.recent_trades = []  # list of step indices when trades were opened
        
    def calculate(
        self,
        pnl_change:    float,   # change in unrealized PnL this step
        unrealized_pnl: float,  # current total unrealized PnL
        position:      int,     # 0=flat, 1=long, -1=short
        opened_trade:  bool,    # did agent just open a trade this step?
        closed_trade:  bool,    # did agent just close a trade this step?
        equity:        float,   # current total equity
        initial_balance: float, # starting balance
        current_step:  int = 0, # current step index (for sliding window)
    ) -> float:
        """
        Calculate shaped reward for one step.

        Returns:
            float — shaped reward signal
        """
        reward = 0.0

        # 1. Base PnL reward
        reward += pnl_change

        # 2. Spread cost — deduct when opening OR closing a trade
        if opened_trade or closed_trade:
            spread_cost = self.spread_pips * self.pip_value
            reward -= spread_cost

        # 2b. Profit bonus - reward closing profitable trades
        if closed_trade and unrealized_pnl > 0:
            reward += self.profit_bonus

        # 3. Hold penalty — penalise sitting in a losing position
        if position != 0 and unrealized_pnl < 0:
            reward -= self.hold_penalty

        # 3b. Overtrading penalty - penalize opening too many trades RECENTLY
        if opened_trade:
            # Record this trade opening step
            self.recent_trades.append(current_step)
            
            # Remove trades outside the recent window
            self.recent_trades = [step for step in self.recent_trades 
                                  if current_step - step < self.overtrade_window]
            
            # Check if exceeded max trades in recent window
            if len(self.recent_trades) > self.max_trades_in_window:
                reward -= self.overtrade_penalty

        # 4. Drawdown penalty — punish large equity drops (only if >2%)
        drawdown = (initial_balance - equity) / initial_balance
        if drawdown > 0.02:   # only penalise drawdown > 2%
            reward -= drawdown * self.drawdown_penalty

        # 5. Risk/reward enforcement - bonus for good risk/reward trades
        if closed_trade and unrealized_pnl > 0:
            spread_cost = self.spread_pips * self.pip_value
            if unrealized_pnl > 1.5 * spread_cost:
                reward += 0.05  # small bonus for good risk/reward ratio

        return reward
    
    def reset(self):
        """Reset the trade tracker at the start of a new episode."""
        self.recent_trades = []
# training/environment/reward_function.py


class RewardFunction:
    """
    Calculates shaped reward signal for the PPO agent.
    Combines PnL reward with penalties to prevent reward hacking.
    """

    def __init__(
        self,
        spread_pips:       float = 1.5,   # typical EUR/USD spread
        hold_penalty:      float = 0.01,  # penalty per step in losing trade
        drawdown_penalty:  float = 2.0,   # multiplier for drawdown punishment
        pip_value:         float = 0.10,
    ):
        self.spread_pips = spread_pips
        self.hold_penalty = hold_penalty
        self.drawdown_penalty = drawdown_penalty
        self.pip_value = pip_value

    def calculate(
        self,
        pnl_change:    float,   # change in unrealized PnL this step
        unrealized_pnl: float,  # current total unrealized PnL
        position:      int,     # 0=flat, 1=long, -1=short
        opened_trade:  bool,    # did agent just open a trade this step?
        closed_trade:  bool,    # did agent just close a trade this step?
        equity:        float,   # current total equity
        initial_balance: float, # starting balance
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

        # 3. Hold penalty — penalise sitting in a losing position
        if position != 0 and unrealized_pnl < 0:
            reward -= self.hold_penalty

        # 4. Drawdown penalty — punish large equity drops
        drawdown = (initial_balance - equity) / initial_balance
        if drawdown > 0:   # only penalise if equity below starting balance
            reward -= drawdown * self.drawdown_penalty

        return reward
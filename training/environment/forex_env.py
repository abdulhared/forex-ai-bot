import gymnasium as gym
import numpy as np
from gymnasium import spaces


class ForexEnv(gym.Env):
    """
    Custom Gym environment simulating Forex trading.
    Observation: 20-element feature vector
    Actions: 0=BUY, 1=HOLD, 2=SELL
    Reward: Change in unrealized PnL per step
    """

    def __init__(self, feature_matrix: np.ndarray, pip_value: float = 0.10):
        """
        Args:
            feature_matrix: Shape [n_candles, 20] — pre-built feature vectors
            pip_value:       Dollar value per pip per 0.01 lot (default $0.10)
        """
        super().__init__()

        # Data
        self.feature_matrix = feature_matrix
        self.pip_value = pip_value
        self.n_candles = feature_matrix.shape[0]

        # Gym spaces
        self.action_space = spaces.Discrete(3)  # 0=BUY, 1=HOLD, 2=SELL
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(20,),
            dtype=np.float32
        )

        # Episode state
        self.current_step = None
        self.episode_step = None
        self.entry_price = None
        self.position = None  # 0=flat, 1=long, -1=short
        self.balance = None
        self.unrealized_pnl = None
        self.initial_balance = 10_000.0

    def reset(self, seed=None):
        """Start a new episode at a random point in the data."""
        super().reset(seed=seed)

        # Pick random starting point — leave room for episode
        self.current_step = np.random.randint(0, self.n_candles - 200)
        self.episode_step = 0
        self.entry_price = None
        self.position = 0
        self.balance = self.initial_balance
        self.unrealized_pnl = 0.0

        observation = self.feature_matrix[self.current_step]
        return observation, {}

    def step(self, action: int):
        """
        Execute one step in the environment.

        Args:
            action: 0=BUY, 1=HOLD, 2=SELL

        Returns:
            observation, reward, terminated, truncated, info
        """
        current_features = self.feature_matrix[self.current_step]
        close_price = current_features[0]  # index 0 = normalised close

        # Default reward is change in unrealized PnL
        reward = 0.0
        prev_unrealized = self.unrealized_pnl

        # --- Handle position closing (BUY or SELL while in position) ---
        if (action == 0 and self.position == -1) or (action == 2 and self.position == 1):
            # Close position — realize PnL
            self.balance += self.unrealized_pnl
            self.position = 0
            self.entry_price = None
            self.unrealized_pnl = 0.0

        # --- Open new position if flat ---
        elif action == 0 and self.position == 0:
            self.position = 1
            self.entry_price = close_price

        elif action == 2 and self.position == 0:
            self.position = -1
            self.entry_price = close_price

        # --- Calculate unrealized PnL for open position ---
        if self.position == 1:   # long
            pip_size = 0.0001
            self.unrealized_pnl = (close_price - self.entry_price) / pip_size * self.pip_value

        elif self.position == -1:  # short
            pip_size = 0.0001
            self.unrealized_pnl = (self.entry_price - close_price) / pip_size * self.pip_value

        # Reward is change in unrealized PnL (0 if flat)
        reward = self.unrealized_pnl - prev_unrealized

        # Advance steps
        self.current_step += 1
        self.episode_step += 1

        # Check termination conditions
        total_equity = self.balance + self.unrealized_pnl
        terminated = (
            total_equity < self.initial_balance * 0.9 or  # 10% drawdown
            self.current_step >= self.n_candles - 1       # end of data
        )
        truncated = self.episode_step >= 200  # max 200 steps per episode

        observation = self.feature_matrix[
            min(self.current_step, self.n_candles - 1)
        ]

        info = {
            "balance": self.balance,
            "unrealized_pnl": self.unrealized_pnl,
            "total_equity": total_equity,
            "position": self.position,
            "step": self.current_step,
            "episode_step": self.episode_step,
        }

        return observation, reward, terminated, truncated, info
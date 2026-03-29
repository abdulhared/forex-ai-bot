# training/model/trainer.py

import torch
import numpy as np

from training.environment.forex_env import ForexEnv
from training.environment.reward_function import RewardFunction
from training.model.ppo_agent import PPOAgent
from app.infrastructure.monitoring.logger import setup_logger


class Trainer:
    """
    Orchestrates PPO training loop.
    Collects rollouts, triggers updates, logs progress.
    """

    def __init__(
        self,
        feature_matrix: np.ndarray,
        rollout_steps: int = 2048,
        total_steps: int = 1_000_000,
    ):
        # Environment
        self.env = ForexEnv(feature_matrix)

        # Reward shaping
        self.reward_fn = RewardFunction()

        # PPO agent
        self.agent = PPOAgent()

        # Logger
        self.logger = setup_logger()

        # Training config
        self.rollout_steps = rollout_steps
        self.total_steps = total_steps

    # ---------------------------------------------------------

    def train(self):
        """Main training loop."""

        self.logger.info(
            f"Training started | "
            f"total_steps={self.total_steps} | "
            f"rollout_steps={self.rollout_steps}"
        )

        # Initial reset
        state, _ = self.env.reset()

        episode = 0
        step = 0
        ep_reward = 0.0

        # Training loop
        while step < self.total_steps:

            # ── Collect one rollout ──────────────────
            for _ in range(self.rollout_steps):

                action, log_prob, value = \
                    self.agent.select_action(state)

                (
                    next_state,
                    raw_reward,
                    terminated,
                    truncated,
                    info,
                ) = self.env.step(action)

                # Reward shaping
                reward = self.reward_fn.calculate(
                    pnl_change=raw_reward,
                    unrealized_pnl=info["unrealized_pnl"],
                    position=info["position"],
                    opened_trade=False,
                    closed_trade=False,
                    equity=info["equity"],
                    initial_balance=10_000.0,
                )

                # Store experience
                self.agent.store(
                    state,
                    action,
                    reward,
                    log_prob,
                    value,
                    terminated or truncated,
                )

                # Update trackers
                ep_reward += reward
                state = next_state
                step += 1

                done = terminated or truncated

                # Episode finished
                if done:

                    state, _ = self.env.reset()

                    self.logger.info(
                        f"Episode {episode} | "
                        f"reward={ep_reward:.2f} | "
                        f"step={step}"
                    )

                    episode += 1
                    ep_reward = 0.0

                # Stop if max steps reached
                if step >= self.total_steps:
                    break

            # ── Update policy ────────────────────────
            self.agent.update()

        self.logger.info("Training complete")

        return self.agent.model
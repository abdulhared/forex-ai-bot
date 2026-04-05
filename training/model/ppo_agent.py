# training/model/ppo_agent.py

import torch
import torch.nn as nn
import numpy as np

from training.model.actor_critic import ActorCritic
from training.model.memory_buffer import MemoryBuffer
from app.infrastructure.monitoring.logger import setup_logger


class PPOAgent:
    """
    PPO algorithm implementation.
    Collects rollouts, computes advantages, updates Actor-Critic network.
    """

    def __init__(
        self,
        input_dim:   int   = 20,
        hidden_dim:  int   = 128,
        n_actions:   int   = 3,
        lr:          float = 3e-5,  
        gamma:       float = 0.99,
        epsilon:     float = 0.2,
        epochs:      int   = 8,
        batch_size:  int   = 128,
    ):

        # Hyperparameters
        self.gamma      = gamma
        self.epsilon    = epsilon
        self.epochs     = epochs
        self.batch_size = batch_size

        # Model
        self.model = ActorCritic(
            input_dim,
            hidden_dim,
            n_actions
        )

        # Experience buffer
        self.buffer = MemoryBuffer()

        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=lr
        )

        # Logger
        self.logger = setup_logger()

    # ---------------------------------------------------------

    def select_action(self, state: np.ndarray):
        """
        Sample action from policy given current state.

        Returns:
            action, log_prob, value
        """

        state_tensor = torch.tensor(
            state,
            dtype=torch.float32
        ).unsqueeze(0)

        with torch.no_grad():
            action_probs, value = self.model(
                state_tensor
            )

        # Create distribution
        dist = torch.distributions.Categorical(
            action_probs
        )

        # Sample action
        action = dist.sample()

        log_prob = dist.log_prob(
            action
        )

        return (
            action.item(),
            log_prob,
            value.squeeze()
        )

    # ---------------------------------------------------------

    def store(
        self,
        state,
        action,
        reward,
        log_prob,
        value,
        done
    ):
        """Store experience in buffer."""

        self.buffer.store(
            state,
            action,
            reward,
            log_prob,
            value,
            done
        )

    # ---------------------------------------------------------

    def _compute_returns(
        self,
        rewards: torch.Tensor,
        dones: torch.Tensor,
        last_value: float
    ) -> torch.Tensor:
        """
        Compute discounted returns using gamma.
        Works backwards from end of episode.
        """

        returns = []

        R = last_value

        for reward, done in zip(
            reversed(rewards),
            reversed(dones)
        ):

            R = (
                reward
                + self.gamma
                * R
                * (1 - done)
            )

            returns.insert(0, R)

        return torch.tensor(
            returns,
            dtype=torch.float32
        )

    # ---------------------------------------------------------

    def update(self):
        """
        Run PPO update on collected experiences.
        """

        (
            states,
            actions,
            rewards,
            old_log_probs,
            values,
            dones
        ) = self.buffer.get()

        # -------------------------------------

        returns = self._compute_returns(
            rewards,
            dones,
            last_value=0.0
        )

        advantages = returns - values

        # Advantage normalization
        advantages = (
            advantages
            - advantages.mean()
        ) / (
            advantages.std()
            + 1e-8
        )

        # -------------------------------------

        for _ in range(self.epochs):

            indices = torch.randperm(
                len(states)
            )

            for start in range(
                0,
                len(states),
                self.batch_size
            ):

                batch_idx = indices[
                    start:
                    start + self.batch_size
                ]

                b_states = states[batch_idx]

                b_actions = actions[batch_idx]

                b_old_lp = old_log_probs[
                    batch_idx
                ]

                b_advantages = advantages[
                    batch_idx
                ]

                b_returns = returns[
                    batch_idx
                ]

                # -------------------------

                action_probs, b_values = self.model(
                    b_states
                )

                dist = torch.distributions.Categorical(
                    action_probs
                )

                new_log_probs = dist.log_prob(
                    b_actions
                )

                entropy = dist.entropy()

                # -------------------------

                ratio = torch.exp(
                    new_log_probs
                    - b_old_lp
                )

                # PPO clipped objective

                surr1 = ratio * b_advantages

                surr2 = torch.clamp(
                    ratio,
                    1 - self.epsilon,
                    1 + self.epsilon
                ) * b_advantages

                actor_loss = -torch.mean(
                    torch.min(
                        surr1,
                        surr2
                    )
                )

                # -------------------------

                critic_loss = nn.MSELoss()(
                    b_values.squeeze(-1),
                    b_returns
                )

                # -------------------------

                entropy_loss = -torch.mean(
                    entropy
                )

                # -------------------------

                loss = (
                    actor_loss
                    + 0.5 * critic_loss
                    + 0.01 * entropy_loss
                )

                # Backprop

                self.optimizer.zero_grad()

                loss.backward()

                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=0.5)
                
                self.optimizer.step()

        # Clear buffer

        self.buffer.clear()

        self.logger.info(
            f"PPO update complete | loss={loss.item():.4f}"
        )
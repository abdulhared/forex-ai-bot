# training/model/memory_buffer.py

import torch
import numpy as np


class MemoryBuffer:
    """
    Stores PPO rollout experiences.
    Cleared after each policy update.
    """

    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

    def store(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        log_prob: torch.Tensor,
        value: torch.Tensor,
        done: bool,
    ) -> None:
        """Store one step of experience."""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob.detach())  # detach from computation graph
        self.values.append(value.detach())
        self.dones.append(done)

    def get(self):
        """
        Return all stored experiences as tensors.

        Returns:
            Tuple of tensors ready for PPO update
        """
        states = torch.tensor(np.array(self.states), dtype=torch.float32)
        actions = torch.tensor(self.actions, dtype=torch.long)
        rewards = torch.tensor(self.rewards, dtype=torch.float32)
        log_probs = torch.stack(self.log_probs)   # already tensors — use stack not tensor()
        values = torch.stack(self.values)
        dones = torch.tensor(self.dones, dtype=torch.float32)

        return states, actions, rewards, log_probs, values, dones

    def clear(self) -> None:
        """Clear buffer after policy update."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

    def __len__(self) -> int:
        """Return number of stored experiences."""
        return len(self.states)
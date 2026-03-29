# training/model/actor_critic.py

import torch
import torch.nn as nn


class ActorCritic(nn.Module):
    """
    Shared-backbone Actor-Critic network for PPO.
    Input:  20-element feature vector
    Output: action probabilities (Actor) + state value (Critic)
    """

    def __init__(self, input_dim: int = 20, hidden_dim: int = 128, n_actions: int = 3):
        super().__init__()

        # Shared layers — learn market representations
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Actor head — outputs action probabilities
        self.actor_head = nn.Linear(hidden_dim, n_actions)

        # Critic head — outputs single value estimate
        self.critic_head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor):
        """
        Forward pass.

        Args:
            x: Input tensor of shape [batch, 20]

        Returns:
            action_probs: Tensor [batch, 3]
            value:        Tensor [batch, 1]
        """
        # 1. Pass through shared layers
        shared_out = self.shared(x)

        # 2. Actor — softmax over actions
        action_logits = self.actor_head(shared_out)
        action_probs = torch.softmax(action_logits, dim=1)

        # 3. Critic — single value output
        value = self.critic_head(shared_out)

        return action_probs, value
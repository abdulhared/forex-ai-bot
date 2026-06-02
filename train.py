# train.py — Local test training (10k steps, ~10-15 minutes)

import numpy as np
import torch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from training.data.dataset_builder import DatasetBuilder
from training.environment.forex_env import ForexEnv
from training.model.ppo_agent import PPOAgent


def main():
    print("=" * 60)
    print("FOREX AI BOT — Local Test Training")
    print("=" * 60)
    
    # 1. Load features
    print("\n[1/5] Loading feature matrix...")
    builder = DatasetBuilder()
    features = builder.load("data/features/eurusd_2020_2022")
    print(f"      Shape: {features.shape}")
    print(f"      Samples: {features.shape[0]:,}")
    
    # 2. Create environment
    print("\n[2/5] Creating trading environment...")
    env = ForexEnv(features, pip_value=0.10)
    print(f"      Action space: {env.action_space}")
    print(f"      Observation space: {env.observation_space}")
    
    # 3. Initialize agent
    print("\n[3/5] Initializing PPO agent...")
    agent = PPOAgent(
        input_dim=20,
        hidden_dim=128,
        n_actions=3,
        lr=1e-4,
        gamma=0.99,
        epsilon=0.2,
        epochs=4, 
        batch_size=64
    )
    print(f"      Model: Actor-Critic (20 -> 128 -> 3)")
    print(f"      Hyperparams: lr=1e-4, gamma=0.99, epsilon=0.2")
    
    # 4. Training loop (2M steps for quick test)
    print("\n[4/5] Starting training (2,000,000 steps)...")
    total_timesteps =2_000_000
    episode_rewards = []
    
    state, _ = env.reset()
    episode_reward = 0
    
    for step in range(total_timesteps):
        # Select action
        action, log_prob, value = agent.select_action(state)
        
        # Step environment
        next_state, reward, terminated, truncated, info = env.step(action)
        
        # Store experience
        agent.store(state, action, reward, log_prob, value, terminated)
        
        episode_reward += reward
        state = next_state
        
        # Episode end
        if terminated or truncated:
            episode_rewards.append(episode_reward)
            
            # Update every 2048 steps or at episode end
            if len(agent.buffer.states) >= 2048:
                agent.update()
            
            # Reset
            state, _ = env.reset()
            episode_reward = 0
            
            # Progress log
            if len(episode_rewards) % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                print(f"      Step {step}/{total_timesteps} | "
                      f"Episodes: {len(episode_rewards)} | "
                      f"Avg Reward (last 10): {avg_reward:.2f}")
    
    # Final update if buffer has data
    if len(agent.buffer.states) > 0:
        agent.update()
    
    # 5. Save model
    print("\n[5/5] Saving model...")
    save_path = "models/ppo_eurusd_2020-2022.pt"
    torch.save(agent.model.state_dict(), save_path)
    print(f"      Saved to: {save_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Total episodes: {len(episode_rewards)}")
    print(f"Average reward: {np.mean(episode_rewards):.2f}")
    print(f"Best episode: {max(episode_rewards):.2f}")
    print(f"Worst episode: {min(episode_rewards):.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
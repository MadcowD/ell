import gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from gym.vector import AsyncVectorEnv
import random

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Hyperparameters
NUM_ENVIRONMENTS = 4           # Reduced for simplicity
NUM_ITERATIONS = 50            # Number of training iterations
TRAJECTORIES_PER_ITER = 100    # Total number of trajectories per iteration
ELITE_PERCENT = 10             # Top k% trajectories to select
LEARNING_RATE = 1e-3
BATCH_SIZE = 64
MAX_STEPS = 500                # Max steps per trajectory
ENV_NAME = 'CartPole-v1'       # Gym environment

# Define the Policy Network


class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(PolicyNetwork, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

    def forward(self, state):
        logits = self.fc(state)
        return logits

    def get_action(self, state):
        logits = self.forward(state)
        action_probs = torch.softmax(logits, dim=-1)
        action = torch.multinomial(action_probs, num_samples=1)
        return action.squeeze(-1)

# Function to create multiple environments


def make_env(env_name, seed):
    def _init():
        env = gym.make(env_name)
        return env
    return _init


def collect_trajectories(envs, policy, num_trajectories, max_steps):
    trajectories = []
    num_envs = envs.num_envs

    # Handle the return type of reset()
    reset_output = envs.reset()
    if isinstance(reset_output, tuple) or isinstance(reset_output, list):
        obs = reset_output[0]  # Extract observations
    else:
        obs = reset_output

    done_envs = [False] * num_envs
    steps = 0

    # Initialize storage for states, actions, and rewards per environment
    env_states = [[] for _ in range(num_envs)]
    env_actions = [[] for _ in range(num_envs)]
    env_rewards = [0.0 for _ in range(num_envs)]
    total_collected = 0

    while total_collected < num_trajectories and steps < max_steps:
        # Convert observations to tensor efficiently
        try:
            # Ensure 'obs' is a NumPy array
            if not isinstance(obs, np.ndarray):
                print(f"Unexpected type for observations: {type(obs)}")
                raise ValueError("Observations are not a NumPy array.")

            # Convert observations to tensor using from_numpy for efficiency
            obs_tensor = torch.from_numpy(obs).float()
            # Ensure the observation dimension matches expected
            assert obs_tensor.shape[1] == 4, f"Expected observation dimension 4, got {
                obs_tensor.shape[1]}"
        except Exception as e:
            print(f"Error converting observations to tensor at step {
                  steps}: {e}")
            print(f"Observations: {obs}")
            raise e

        with torch.no_grad():
            actions = policy.get_action(obs_tensor).cpu().numpy()

        # Unpack step based on Gym version
        try:
            # For Gym versions >=0.26, step returns five values
            next_obs, rewards, dones, truncs, infos = envs.step(actions)
        except ValueError:
            # For older Gym versions, step returns four values
            next_obs, rewards, dones, infos = envs.step(actions)
            # Assume no truncations if not provided
            truncs = [False] * len(dones)

        # Handle the reset output of step()
        if isinstance(next_obs, tuple) or isinstance(next_obs, list):
            next_obs = next_obs[0]  # Extract observations

        # Ensure infos is a list
        if not isinstance(infos, list):
            infos = [{} for _ in range(num_envs)]  # Default to empty dicts

        for i in range(num_envs):
            if not done_envs[i]:
                # Check if obs[i] has the correct shape
                if len(obs[i]) != 4:
                    print(f"Unexpected observation shape for env {
                          i}: {obs[i]}")
                    continue  # Skip this step for the problematic environment

                env_states[i].append(obs[i])
                env_actions[i].append(actions[i])
                env_rewards[i] += rewards[i]
                if dones[i] or truncs[i]:
                    # Extract reward from infos
                    if isinstance(infos[i], dict):
                        episode_info = infos[i].get('episode', {})
                        traj_reward = episode_info.get(
                            'r') if 'r' in episode_info else env_rewards[i]
                    else:
                        # Handle cases where infos[i] is not a dict
                        traj_reward = env_rewards[i]
                        print(f"Warning: infos[{i}] is not a dict. Received type: {
                              type(infos[i])}")

                    trajectories.append({
                        'states': env_states[i],
                        'actions': env_actions[i],
                        'reward': traj_reward
                    })
                    total_collected += 1
                    env_states[i] = []
                    env_actions[i] = []
                    env_rewards[i] = 0.0
                    done_envs[i] = True

        obs = next_obs
        steps += 1

        # Reset environments that are done
        if any(done_envs):
            indices = [i for i, done in enumerate(done_envs) if done]
            if total_collected < num_trajectories:
                for i in indices:
                    try:
                        # Directly reset the environment
                        reset_output = envs.envs[i].reset()
                        if isinstance(reset_output, tuple) or isinstance(reset_output, list):
                            # For Gym versions where reset returns (obs, info)
                            obs[i] = reset_output[0]
                        else:
                            # For Gym versions where reset returns only obs
                            obs[i] = reset_output
                        done_envs[i] = False
                    except Exception as e:
                        print(f"Error resetting environment {i}: {e}")
                        # Optionally, handle the failure (e.g., retry, terminate the environment)
                        done_envs[i] = False  # Prevent infinite loop

    return trajectories


def select_elite(trajectories, percentile=ELITE_PERCENT):
    rewards = [traj['reward'] for traj in trajectories]
    if not rewards:
        return []
    reward_threshold = np.percentile(rewards, 100 - percentile)
    elite_trajectories = [
        traj for traj in trajectories if traj['reward'] >= reward_threshold]
    return elite_trajectories

# Function to create training dataset from elite trajectories


def create_training_data(elite_trajectories):
    states = []
    actions = []
    for traj in elite_trajectories:
        states.extend(traj['states'])
        actions.extend(traj['actions'])
    if not states or not actions:
        return None, None
    # Convert lists to NumPy arrays first for efficiency
    states = np.array(states, dtype=np.float32)
    actions = np.array(actions, dtype=np.int64)
    # Convert to PyTorch tensors
    states = torch.from_numpy(states)
    actions = torch.from_numpy(actions)
    return states, actions


# Main execution code
if __name__ == '__main__':
    # Initialize environments
    env_fns = [make_env(ENV_NAME, SEED + i) for i in range(NUM_ENVIRONMENTS)]
    envs = AsyncVectorEnv(env_fns)

    # Get environment details
    dummy_env = gym.make(ENV_NAME)
    state_dim = dummy_env.observation_space.shape[0]
    action_dim = dummy_env.action_space.n
    dummy_env.close()

    # Initialize policy network and optimizer
    policy = PolicyNetwork(state_dim, action_dim)
    optimizer = optim.Adam(policy.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    # Training Loop
    for iteration in range(1, NUM_ITERATIONS + 1):
        try:
            # Step 1: Collect Trajectories
            trajectories = collect_trajectories(
                envs, policy, TRAJECTORIES_PER_ITER, MAX_STEPS)
        except Exception as e:
            print(f"Error during trajectory collection at iteration {
                  iteration}: {e}")
            break

        # Step 2: Select Elite Trajectories
        elite_trajectories = select_elite(trajectories, ELITE_PERCENT)

        if len(elite_trajectories) == 0:
            print(f"Iteration {
                  iteration}: No elite trajectories found. Skipping update.")
            continue

        # Step 3: Create Training Data
        states, actions = create_training_data(elite_trajectories)

        if states is None or actions is None:
            print(f"Iteration {
                  iteration}: No training data available. Skipping update.")
            continue

        # Step 4: Behavioral Cloning (Policy Update)
        dataset_size = states.size(0)
        indices = np.arange(dataset_size)
        np.random.shuffle(indices)

        for start in range(0, dataset_size, BATCH_SIZE):
            end = start + BATCH_SIZE
            batch_indices = indices[start:end]
            batch_states = states[batch_indices]
            batch_actions = actions[batch_indices]

            optimizer.zero_grad()
            logits = policy(batch_states)
            loss = criterion(logits, batch_actions)
            loss.backward()
            optimizer.step()

        # Step 5: Evaluate Current Policy
        avg_reward = np.mean([traj['reward'] for traj in elite_trajectories])
        print(f"Iteration {iteration}: Elite Trajectories: {
              len(elite_trajectories)}, Average Reward: {avg_reward:.2f}")

    # Close environments
    envs.close()

    # Testing the Trained Policy
    def test_policy(policy, env_name=ENV_NAME, episodes=5, max_steps=500):
        env = gym.make(env_name)
        total_rewards = []
        for episode in range(episodes):
            obs, _ = env.reset()
            done = False
            episode_reward = 0
            for _ in range(max_steps):
                obs_tensor = torch.from_numpy(obs).float().unsqueeze(0)
                with torch.no_grad():
                    action = policy.get_action(obs_tensor).item()
                obs, reward, done, info, _ = env.step(action)
                episode_reward += reward
                if done:
                    break
            total_rewards.append(episode_reward)
            print(f"Test Episode {episode + 1}: Reward: {episode_reward}")
        env.close()
        print(f"Average Test Reward over {episodes} episodes: {
              np.mean(total_rewards):.2f}")

    # Run the test
    test_policy(policy)

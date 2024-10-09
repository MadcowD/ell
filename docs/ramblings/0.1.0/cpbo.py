import gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import namedtuple
from torch.utils.data import DataLoader, TensorDataset

# Define a simple policy network


class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(PolicyNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)  # Output action probabilities
        )

    def forward(self, x):
        return self.network(x)

# Function to collect trajectories


def collect_trajectories(env, policy, num_episodes, device):
    trajectories = []
    Episode = namedtuple('Episode', ['states', 'actions', 'rewards'])

    for episode_num in range(num_episodes):
        states = []
        actions = []
        rewards = []
        # Handle Gym's updated reset() API
        # Optional: set seed for reproducibility
        state, info = env.reset(seed=42 + episode_num)
        done = False

        while not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            with torch.no_grad():
                action_probs = policy(state_tensor)
            action_dist = torch.distributions.Categorical(action_probs)
            action = action_dist.sample().item()

            # Handle Gym's updated step() API
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            states.append(state)
            actions.append(action)
            rewards.append(reward)

            state = next_state

        trajectories.append(Episode(states, actions, rewards))

    return trajectories

# Function to compute returns


def compute_returns(trajectories, gamma=0.99):
    all_returns = []
    for episode in trajectories:
        returns = []
        G = 0
        for reward in reversed(episode.rewards):
            G = reward + gamma * G
            returns.insert(0, G)
        all_returns.extend(returns)
    return all_returns

# Function to create labeled dataset


def create_labeled_dataset(trajectories, gamma=0.99, device='cpu'):
    states = []
    actions = []
    labels = []

    all_returns = compute_returns(trajectories, gamma)
    all_returns = np.array(all_returns)
    median_return = np.median(all_returns)

    for episode in trajectories:
        for t in range(len(episode.rewards)):
            # Compute return from timestep t
            G = sum([gamma**k * episode.rewards[t + k]
                    for k in range(len(episode.rewards) - t)])
            label = 1 if G >= median_return else 0
            states.append(episode.states[t])
            actions.append(episode.actions[t])
            labels.append(label)

    # Convert lists to NumPy arrays first for efficiency
    states = np.array(states)
    actions = np.array(actions)
    labels = np.array(labels)

    # Convert to PyTorch tensors
    states = torch.FloatTensor(states).to(device)
    actions = torch.LongTensor(actions).to(device)
    labels = torch.FloatTensor(labels).to(device)

    return states, actions, labels

# Function to perform behavioral cloning update


def behavioral_cloning_update(policy, optimizer, dataloader, device):
    criterion = nn.BCELoss()
    policy.train()

    for states, actions, labels in dataloader:
        optimizer.zero_grad()
        action_probs = policy(states)
        # Gather the probability of the taken action
        selected_probs = action_probs.gather(
            1, actions.unsqueeze(1)).squeeze(1)
        # Labels are 1 for good actions, 0 for bad actions
        loss = criterion(selected_probs, labels)
        loss.backward()
        optimizer.step()

# Evaluation function


def evaluate_policy(env, policy, device, episodes=5):
    policy.eval()
    total_rewards = []
    for _ in range(episodes):
        state, info = env.reset()
        done = False
        ep_reward = 0
        while not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            with torch.no_grad():
                action_probs = policy(state_tensor)
            action = torch.argmax(action_probs, dim=1).item()
            # Handle Gym's updated step() API
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            ep_reward += reward
            state = next_state
        total_rewards.append(ep_reward)
    average_reward = np.mean(total_rewards)
    return average_reward

# Main CBPO algorithm


def CBPO(env_name='CartPole-v1', num_epochs=10, num_episodes_per_epoch=100, gamma=0.99,
         batch_size=64, learning_rate=1e-3, device='cpu'):

    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    policy = PolicyNetwork(state_dim, action_dim).to(device)
    optimizer = optim.Adam(policy.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")

        # 1. Collect trajectories
        trajectories = collect_trajectories(
            env, policy, num_episodes_per_epoch, device)

        # 2. Create labeled dataset
        states, actions, labels = create_labeled_dataset(
            trajectories, gamma, device)

        # 3. Create DataLoader
        dataset = TensorDataset(states, actions, labels)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # 4. Behavioral Cloning Update
        behavioral_cloning_update(policy, optimizer, dataloader, device)

        # 5. Evaluate current policy
        avg_reward = evaluate_policy(env, policy, device)
        print(f"Average Reward: {avg_reward}")

        # Early stopping if solved
        if avg_reward >= env.spec.reward_threshold:
            print(f"Environment solved in {epoch+1} epochs!")
            break

    env.close()
    return policy


if __name__ == "__main__":
    # Check if GPU is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Run CBPO
    trained_policy = CBPO(
        env_name='CartPole-v1',
        num_epochs=50,
        num_episodes_per_epoch=500,
        gamma=0.99,
        batch_size=64,
        learning_rate=1e-3,
        device=device
    )

    # Final Evaluation
    env = gym.make('CartPole-v1')
    final_avg_reward = evaluate_policy(
        env, trained_policy, device, episodes=20)
    print(f"Final Average Reward over 20 episodes: {final_avg_reward}")
    env.close()

    # Save the trained policy
    torch.save(trained_policy.state_dict(), "trained_cartpole_policy.pth")
    print("Trained policy saved to trained_cartpole_policy.pth")

    # Demo the trained policy with rendering
    env = gym.make('CartPole-v1', render_mode='human')
    state, _ = env.reset()
    done = False
    total_reward = 0

    while not done:
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
        action = trained_policy(state_tensor).argmax().item()
        state, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        done = terminated or truncated
        env.render()

    print(f"Demo episode finished with total reward: {total_reward}")
    env.close()

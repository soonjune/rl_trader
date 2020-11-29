import numpy as np
import torch
import torch.nn as nn
import numpy as np

from replay_memory import ReplayBuffer
from deep_q_network import MLP

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


def predict(model, np_states):
    model.eval()

    with torch.no_grad():
        inputs = torch.from_numpy(np_states.astype(np.float32)).to(device)
        output = model(inputs).to(device)
        # print("output:", output)
        return output.cpu().numpy()


def train_one_step(model, criterion, optimizer, inputs, targets):
    model.train()
    # convert to tensors
    inputs = torch.from_numpy(inputs.astype(np.float32)).to(device)
    targets = torch.from_numpy(targets.astype(np.float32)).to(device)

    # zero the parameter gradients
    optimizer.zero_grad()

    # Forward pass
    outputs = model(inputs)
    loss = criterion(outputs, targets).to(device)

    # Backward and optimize
    loss.backward()
    optimizer.step()


class DQNAgent(object):
    def __init__(self, state_size, action_size):
        self.state_size = state_size # input size
        self.action_size = action_size # output size
        self.memory = ReplayBuffer(state_size, action_size, size=500)
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.model = MLP(state_size, action_size).to(device)

        # Loss and optimizer
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters())


    def update_replay_memory(self, state, action, reward, next_state, done):
        self.memory.store(state, action, reward, next_state, done)

    def act(self, state):
        if np.random.rand() <= self.epsilon: # epsilon greedy
            return np.random.choice(self.action_size)
        act_values = predict(self.model, state)
        return np.argmax(act_values[0])  # returns (greedy) action

    def replay(self, batch_size=32):
        # first check if replay buffer contains enough data
        if self.memory.size < batch_size:
            return

        # sample a batch of data from the replay memory
        minibatch = self.memory.sample_batch(batch_size)
        states = minibatch['s']
        actions = minibatch['a']
        rewards = minibatch['r']
        next_states = minibatch['s2']
        done = minibatch['d']

        # Calculate the target: Q(s',a)
        target = rewards + (1 - done) * self.gamma * np.amax(predict(self.model, next_states), axis=1)

        # With the PyTorch API, it is simplest to have the target be the
        # same shape as the predictions.
        # However, we only need to update the network for the actions
        # which were actually taken.
        # We can accomplish this by setting the target to be equal to
        # the prediction for all values.
        # Then, only change the targets for the actions taken.
        # Q(s,a)
        target_full = predict(self.model, states)
        target_full[np.arange(batch_size), actions] = target # double indexing - row, col

        # Run one training step - gradient descent
        train_one_step(self.model, self.criterion, self.optimizer, states, target_full)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)
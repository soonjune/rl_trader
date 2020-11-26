import numpy as np
import pandas as pd

from datetime import datetime
import itertools
import argparse
from math import floor
import pickle

from sklearn.preprocessing import StandardScaler
from utils import maybe_make_dir
from dqn_agent import DQNAgent

# Let's use samsung_elec, lg_elec, hanhwa_aero, naver, kakao
def get_data():
    # returns a T x 3 list of stock prices
    # each row is a different stock
    df = pd.read_csv('black_month.csv')
    return df.values


def get_scaler(env):
    # return scikit-learn scaler object to scale the states
    # Note: you could also populate the replay buffer here
    # run multiple episodes to make it more accurate

    states = []
    for _ in range(env.n_step):
        action = np.random.choice(env.action_space)
        state, reward, done, info = env.step(action)
        states.append(state)
        if done:
            break

    scaler = StandardScaler()
    scaler.fit(states)
    return scaler


class MultiStockEnv:
    """
    A 5-stock trading environment.
    State: vector of size 11 (n_stock * 2 + 1)
      - # shares of stock 1-5 owned
      - price of stock 1-5 (using daily close price)
      - cash owned (can be used to purchase more stocks)
    Action: categorical variable with 243 (3^5) possibilities
      - for each stock, you can:
      - 0 = sell
      - 1 = hold
      - 2 = buy
    """

    def __init__(self, data, initial_investment=50000000, tax_rate=0.0025, fees_rate=0.00015):
        # data
        self.stock_price_history = data
        self.n_step, self.n_stock = self.stock_price_history.shape

        # instance attributes
        self.initial_investment = initial_investment
        self.tax_rate = tax_rate
        self.fees_rate = fees_rate
        self.cur_step = None
        self.stock_owned = None
        self.stock_price = None
        self.cash_in_hand = None

        self.action_space = np.arange(3 ** self.n_stock)

        # action permutations
        # returns a nested list with elements like:
        # [0,0,0,0,0]
        # [0,0,0,0,1]
        # [0,0,0,0,2]
        # [0,0,0,1,0]
        # [0,0,0,1,1]
        # etc.
        # 0 = sell
        # 1 = hold
        # 2 = buy
        self.action_list = list(map(list, itertools.product([0, 1, 2], repeat=self.n_stock)))

        # calculate size of state
        self.state_dim = self.n_stock * 2 + 1

        self.reset()

    def reset(self):
        self.cur_step = 0
        self.stock_owned = np.zeros(self.n_stock)
        self.stock_price = self.stock_price_history[self.cur_step]
        self.cash_in_hand = self.initial_investment
        return self._get_obs()

    def step(self, action):
        assert action in self.action_space

        # get current value before performing the action
        prev_val = self._get_val()

        # update price, i.e. go to the next trading point
        self.cur_step += 1
        self.stock_price = self.stock_price_history[self.cur_step]

        # perform the trade - buy, sell, hold
        self._trade(action)

        # get the new value after taking the action
        cur_val = self._get_val()

        # reward is the increase in porfolio value
        reward = cur_val - prev_val

        # done if we have run out of data
        done = self.cur_step == self.n_step - 1
        # satisficing model
        # if not done:
        #     # done if we reach our goal profit
        #     done = cur_val > self.initial_investment * 1.2

        info = {'cur_val': cur_val}

        # conform to the Gym APIx
        return self._get_obs(), reward, done, info

    def _get_obs(self):
        obs = np.empty(self.state_dim)
        obs[:self.n_stock] = self.stock_owned # size 5
        obs[self.n_stock:2 * self.n_stock] = self.stock_price # size 5
        obs[-1] = self.cash_in_hand
        return obs

    def _get_val(self):
        return self.stock_owned.dot(self.stock_price) + self.cash_in_hand

    def _trade(self, action):
        # index the action we want to perform
        # 0 = sell
        # 1 = hold
        # 2 = buy
        # e.g. [2,1,0, 0, 0] means:
        # buy first stock
        # hold second stock
        # sell third stock
        # sell fourth stock
        # sell fifth stock
        action_vec = self.action_list[action]

        # determine which stocks to buy or sell
        sell_index = []  # stores index of stocks we want to sell
        buy_index = []  # stores index of stocks we want to buy
        for i, a in enumerate(action_vec):
            if a == 0: # sell
                sell_index.append(i)
            elif a == 2: # buy
                buy_index.append(i)

        # sell any stocks we want to sell
        # then buy any stocks we want to buy
        if sell_index:
            # NOTE: to simplify the problem, when we sell, we will sell ALL shares of that stock
            for i in sell_index:
                self.cash_in_hand += self.stock_price[i] * self.stock_owned[i]
                - floor(self.stock_price[i]*self.stock_owned[i] * (self.tax_rate+self.fees_rate) / 10) * 10
                self.stock_owned[i] = 0
        if buy_index:
            # NOTE: when buying, we will loop through each stock we want to buy,
            #       and buy one share at a time until we run out of cash
            per_stock = self.cash_in_hand // len(buy_index)
            for i in buy_index:
                # buy chosen stocks equally
                buying_amount = per_stock // (self.stock_price[i]*(1+self.fees_rate))
                self.stock_owned[i] += buying_amount  # buy one share
                self.cash_in_hand -= floor(self.stock_price[i]*buying_amount*(1+self.fees_rate) / 10) * 10


def play_one_episode(agent, env, is_train):
    # note: after transforming states are already 1xD
    state = env.reset()
    state = scaler.transform([state])
    done = False

    while not done:
        action = agent.act(state)
        next_state, reward, done, info = env.step(action)
        next_state = scaler.transform([next_state])
        if is_train == 'train':
            agent.update_replay_memory(state, action, reward, next_state, done)
            agent.replay(batch_size)
        state = next_state

    return info['cur_val']


if __name__ == '__main__':

    # config
    models_folder = 'rl_trader_models'
    rewards_folder = 'rl_trader_rewards'
    num_episodes = 2000
    batch_size = 32
    initial_investment = 50000000

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, required=True,
                        help='either "train" or "test"')
    args = parser.parse_args()

    maybe_make_dir(models_folder)
    maybe_make_dir(rewards_folder)

    data = get_data() # time series data
    n_timesteps, n_stocks = data.shape

    n_train = n_timesteps // 2

    train_data = data[:n_train]
    test_data = data[n_train:]

    env = MultiStockEnv(train_data, initial_investment)
    state_size = env.state_dim
    action_size = len(env.action_space)
    agent = DQNAgent(state_size, action_size)
    scaler = get_scaler(env)

    # store the final value of the portfolio (end of episode)
    portfolio_value = []

    if args.mode == 'test':
        # then load the previous scaler
        with open(f'{models_folder}/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)

        # remake the env with test data
        env = MultiStockEnv(test_data, initial_investment)

        # make sure epsilon is not 1!
        # no need to run multiple episodes if epsilon = 0, it's deterministic
        agent.epsilon = 0.01

        # load trained weights
        agent.load(f'{models_folder}/dqn.ckpt')

    # play the game num_episodes times
    for e in range(num_episodes):
        t0 = datetime.now()
        val = play_one_episode(agent, env, args.mode)
        dt = datetime.now() - t0
        print(f"episode: {e + 1}/{num_episodes}, episode end value: {val}, duration: {dt}")
        portfolio_value.append(val)  # append episode end portfolio value

    # save the weights when we are done
    if args.mode == 'train':
        # save the DQN
        agent.save(f'{models_folder}/dqn.ckpt')

        # save the scaler
        with open(f'{models_folder}/scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)

    # save portfolio value for each episode
    np.save(f'{rewards_folder}/{args.mode}.npy', portfolio_value)
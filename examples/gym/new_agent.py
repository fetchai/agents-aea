# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
This contains the classes for the agent.

Specifically:
    - a class for a multi-armed bandit model of price.
    - a class for a price model of a good.
    - a simple RL agent.
"""

import gym
import numpy as np
import random
from typing import Dict, Optional, Any

from aea.agent import Agent
from aea.channel.gym import GymChannel, GymConnection, DEFAULT_GYM
from aea.mail.base import Envelope, MailBox
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer
# from env import BanditNArmedRandom
# from bandit_proxy_env import BanditProxyEnv
# import BanditProxyEnv
from examples.gym.bandit_proxy_env import BanditProxyEnv
from examples.gym.proxy_env import ProxyEnv

MAX_ACTIONS = 1000


class PriceBandit(object):
    """A class for a multi-armed bandit model of price."""

    def __init__(self, price: float, beta_a: float = 1.0, beta_b: float = 1.0):
        """
        Instantiate a price bandit object.

        :param price: the price this bandit is modelling
        :param beta_a: the a parameter of the beta distribution
        :param beta_b: the b parameter of the beta distribution
        """
        self.price = price
        # default params imply a uniform random prior
        self.beta_a = beta_a
        self.beta_b = beta_b

    def sample(self) -> float:
        """
        Sample from the bandit.

        :return: the sampled value
        """
        return np.random.beta(self.beta_a, self.beta_b)

    def update(self, outcome: bool) -> None:
        """
        Update the bandit.

        :param outcome: the outcome used for updating
        :return: None
        """
        outcome_int = 1 if outcome else 0  # explicit type conversion
        self.beta_a += outcome_int
        self.beta_b += 1 - outcome_int


class GoodPriceModel(object):
    """A class for a price model of a good."""

    def __init__(self, bound: int = 100):
        """Instantiate a good price model."""
        self.price_bandits = dict(
            (price, PriceBandit(price))
            for price in range(bound + 1))

    def update(self, outcome: bool, price: int) -> None:
        """
        Update the respective bandit.

        :param price: the price to be updated
        :param outcome: the negotiation outcome
        :return: None
        """
        bandit = self.price_bandits[price[0]]
        bandit.update(outcome)

    def get_price_expectation(self) -> int:
        """
        Get best price.

        :return: the winning price
        """
        maxsample = -1
        winning_price = 0
        for price, bandit in self.price_bandits.items():
            sample = bandit.sample()
            if sample > maxsample:
                maxsample = sample
                winning_price = price
        return winning_price


class RLAgent(Agent):
    """This class implements a simple RL agent."""

    def __init__(self, name: str, nb_goods: int) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param nb_goods:  the number of goods

        :return: None
        """
        super().__init__(name, timeout=0)

        self.proxy_env = BanditProxyEnv(self.crypto.public_key)

        self.good_price_models = dict(
            (good_id, GoodPriceModel()) for good_id in range(nb_goods))  # type: Dict[int, GoodPriceModel]
        # self.action_counter = 0
        self.actions = {}  # Dict[int, Tuple[int, int]]

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        action_counter = 0

        while action_counter < MAX_ACTIONS:
            action = self._pick_an_action()
            obs, reward, done, info = self.proxy_env.step(action)
            self._update_state(obs, reward, done, info)
            action_counter += 1

        self.stop()

    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """
        pass

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        pass

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        pass

    def _pick_an_action(self) -> Any:
        """
        Pick an action.

        :return: None
        """
        # Increment the counter
        # self.action_counter += 1

        # Get the good
        good_id = self._get_random_next_good()

        # Pick the best price based on own model.
        good_price_model = self.good_price_models[good_id]
        price = good_price_model.get_price_expectation()

        action = [good_id, np.array([price])]
        print(action)
        # step_id = self.action_counter

        # Store action for step id
        # self.actions[step_id] = action
        #
        # print("step_id={}, action taken: {}".format(step_id, action))

        return action

    def _update_state(self, obs, reward, done, info) -> None:
        """
        Take an action.

        :return: None
        """
        # observation = gym_msg.get("observation")
        # done = gym_msg.get("done")
        # info = gym_msg.get("info")
        # reward = gym_msg.get("reward")
        step_id = info.get("step_id")

        # recover action:
        good_id, price = self.actions[step_id]

        # Update the price model:
        good_price_model = self.good_price_models[good_id]
        good_price_model.update(reward, price)

        # # Take another action if we are below max actions.
        # if self.action_counter < MAX_ACTIONS:
        #     self._pick_an_action()
        # else:
        #     self.stop()

    def _get_random_next_good(self) -> int:
        """Get the next good for trading (randomly)."""
        return random.choice(list(self.good_price_models.keys()))

    # def forward_to_proxy(self):
    #     self.proxy_env.set_mailbox(self.mailbox)


if __name__ == "__main__":
    """Launch the agent."""
    nb_goods = 10
    rl_agent = RLAgent('my_rl_agent', nb_goods)

    try:
        rl_agent.start()
    finally:
        rl_agent.stop()

# proxy env needs public key to create connections

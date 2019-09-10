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
import logging
import numpy as np
from typing import Dict, List, Optional, cast
import random

from aea.agent import Agent
from aea.channel.gym import GymConnection, DEFAULT_GYM
from aea.mail.base import Envelope, MailBox
from aea.protocols.base.message import Message
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer

from env import BanditNArmedRandom

MAX_ACTIONS = 4000

logger = logging.getLogger(__name__)


class PriceBandit(object):
    """A class for a multi-armed bandit model of price."""

    def __init__(self, price: int, beta_a: float = 1.0, beta_b: float = 1.0):
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

    def sample(self) -> int:
        """
        Sample from the bandit.

        :return: the sampled value
        """
        return round(np.random.beta(self.beta_a, self.beta_b))

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

    def __init__(self, nb_prices_per_good: int):
        """
        Instantiate a good price model.

        :param nb_prices_per_good: number of prices per good (starting from 0)
        """
        self.price_bandits = dict(
            (price, PriceBandit(price))
            for price in range(nb_prices_per_good))

    def update(self, outcome: bool, price: int) -> None:
        """
        Update the respective bandit.

        :param price: the price to be updated
        :param outcome: the negotiation outcome
        :return: None
        """
        bandit = self.price_bandits[price]
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
    """This class implements a simple (all-in-one) RL agent."""

    def __init__(self, name: str, gym_env: gym.Env, nb_goods: int, nb_prices_per_good: int,
                 timeout: float = 0.0) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param gym_env: the open ai style gym environment
        :param nb_goods:  the number of goods
        :param nb_prices_per_good: number of prices per good (starting from 0)
        :return: None
        """
        super().__init__(name, timeout=timeout)
        self.mailbox = MailBox(GymConnection(self.crypto.public_key, gym_env))
        self.good_price_models = dict((good_id, GoodPriceModel(nb_prices_per_good)) for good_id in
                                      range(nb_goods))  # type: Dict[int, GoodPriceModel]

        self.action_counter = 0
        self.actions = {}  # type: Dict[int, List[int]]

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
        # we only take an action here once to kick of the message chain.
        if self.action_counter == 0:
            self._take_an_action()

    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """
        while not self.inbox.empty():
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            expected_step_id = self.action_counter
            if envelope is not None:
                if envelope.protocol_id == 'gym':
                    gym_msg = GymSerializer().decode(envelope.message)  # type: Message
                    gym_msg = cast(GymMessage, gym_msg)
                    gym_msg_performative = GymMessage.Performative(gym_msg.get("performative"))
                    gym_msg_step_id = gym_msg.get("step_id")
                    if gym_msg_performative == GymMessage.Performative.PERCEPT and gym_msg_step_id == expected_step_id:
                        self._handle_message(gym_msg)
                    else:
                        raise ValueError(
                            "Unexpected performative {} or step_id: {}".format(gym_msg_step_id, gym_msg_performative))
                else:
                    raise ValueError("Unknown protocol_id: {}".format(envelope.protocol_id))

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

    def _take_an_action(self) -> None:
        """
        Take an action.

        :return: None
        """
        assert self.mailbox is not None, "Cannot take an action without a mailbox."
        # Increment the counter
        self.action_counter += 1

        # Get the good
        good_id = self._get_random_next_good()

        # Pick the best price based on own model.
        good_price_model = self.good_price_models[good_id]
        price = good_price_model.get_price_expectation()

        action = [good_id, price]
        step_id = self.action_counter

        # Store action for step id
        self.actions[step_id] = action

        if step_id % 10 == 0:
            print("Action: step_id='{}' action='{}'".format(step_id, action))
            logger.info("Update: step_id='{}' action='{}'".format(step_id, action))

        # create and serialize the message
        gym_msg = GymMessage(performative=GymMessage.Performative.ACT, action=action, step_id=step_id)
        gym_bytes = GymSerializer().encode(gym_msg)
        self.mailbox.outbox.put_message(to=DEFAULT_GYM, sender=self.crypto.public_key,
                                        protocol_id=GymMessage.protocol_id, message=gym_bytes)

    def _get_random_next_good(self) -> int:
        """Get the next good for trading (randomly)."""
        return random.choice(list(self.good_price_models.keys()))

    def _handle_message(self, gym_msg: GymMessage) -> None:
        """
        Take an action.

        :return: None
        """
        # observation = gym_msg.get("observation")
        # done = gym_msg.get("done")
        # info = gym_msg.get("info")
        reward = cast(bool, gym_msg.get("reward"))
        step_id = cast(int, gym_msg.get("step_id"))
        if step_id % 10 == 0:
            print("Reward: step_id='{}' reward='{}'".format(step_id, reward))
            logger.info("Reward: step_id='{}' action='{}'".format(step_id, reward))

        # recover action:
        good_id, price = self.actions[step_id]

        # Update the price model:
        good_price_model = self.good_price_models[good_id]
        good_price_model.update(reward, price)

        # Take another action if we are below max actions.
        if self.action_counter < MAX_ACTIONS:
            self._take_an_action()
        else:
            self.stop()


def main():
    """Launch the agent."""
    nb_goods = 10
    nb_prices_per_good = 100
    gym_env = BanditNArmedRandom(nb_goods, nb_prices_per_good)
    rl_agent = RLAgent('my_rl_agent', gym_env, nb_goods, nb_prices_per_good)
    try:
        rl_agent.start()
    finally:
        rl_agent.stop()


if __name__ == "__main__":
    main()

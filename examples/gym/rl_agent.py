from examples.gym.env import BanditNArmedRandom
from examples.gym.bandit_proxy_env import BanditProxyEnv
from examples.gym.proxy_env import ProxyEnv

from typing import Any
import random
import numpy as np


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


class RLAgent:

    def __init__(self, nb_goods: int):
        self.good_price_models = dict(
            (good_id, GoodPriceModel()) for good_id in range(nb_goods))  # type: Dict[int, GoodPriceModel]

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

        action = [good_id, price]
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

    def fit(self, proxy_env: ProxyEnv, nb_steps: int):
        action_counter = 0

        while action_counter < nb_steps:
            action = self._pick_an_action()
            obs, reward, done, info = proxy_env.step(action)
            self._update_state(obs, reward, done, info)
            action_counter += 1


# proxy_env.connect(proxy_agent, proxy_agent.outbox, proxy_agent.public_key):

if __name__ == "__main__":
    NB_GOODS = 10
    nb_prices_per_good = 100

    gym_env = BanditNArmedRandom(nb_bandits=NB_GOODS, nb_prices_per_bandit=nb_prices_per_good)
    proxy_env = BanditProxyEnv(gym_env)

    """Launch the agent."""
    rl_agent = RLAgent(nb_goods=NB_GOODS)
    rl_agent.fit(proxy_env, nb_steps=300000)

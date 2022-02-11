# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Training a multi armed bandit rl agent using the aea framework."""

import argparse

from gyms.env import BanditNArmedRandom  # noqa: I201
from proxy.env import ProxyEnv  # noqa: I201
from rl.agent import RLAgent  # noqa: I201


DEFAULT_NB_GOODS = 10
DEFAULT_NB_PRICES_PER_GOOD = 100
DEFAULT_NB_STEPS = 4000

parser = argparse.ArgumentParser("train", description="Train an RL agent.")
parser.add_argument(
    "--nb-steps",
    type=int,
    default=DEFAULT_NB_STEPS,
    help="The number of training steps.",
)
parser.add_argument(
    "--nb-goods", type=int, default=DEFAULT_NB_GOODS, help="The number of goods."
)
parser.add_argument(
    "--nb-prices-per-good",
    type=int,
    default=DEFAULT_NB_PRICES_PER_GOOD,
    help="The number of prices per goods.",
)


if __name__ == "__main__":
    arguments = parser.parse_args()

    # Use any gym.Env compatible environment:
    gym_env = BanditNArmedRandom(
        nb_bandits=arguments.nb_goods, nb_prices_per_bandit=arguments.nb_prices_per_good
    )

    # Pass the gym environment to a proxy environment:
    proxy_env = ProxyEnv(gym_env)

    # Use any RL agent compatible with the gym environment and call the fit method:
    rl_agent = RLAgent(nb_goods=arguments.nb_goods)
    rl_agent.fit(env=proxy_env, nb_steps=arguments.nb_steps)

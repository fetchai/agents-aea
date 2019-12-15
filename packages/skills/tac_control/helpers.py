#!/usr/bin/env python3
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

"""This module contains the helpers methods for the controller agent."""

import math
import numpy as np
import random
from typing import Dict, List, Tuple

QUANTITY_SHIFT = 1  # Any non-negative integer is fine.


def generate_good_id_to_name(nb_goods: int) -> Dict[str, str]:
    """
    Generate ids for things.

    :param nb_goods: the number of things.
    :return: a dictionary mapping goods' ids to names.
    """
    max_number_of_digits = math.ceil(math.log10(nb_goods))
    string_format = 'tac_good_{:0' + str(max_number_of_digits) + '}'
    return {string_format.format(i) + '_id': string_format.format(i) for i in range(nb_goods)}


def determine_scaling_factor(money_endowment: int) -> float:
    """
    Compute the scaling factor based on the money amount.

    :param money_endowment: the endowment of money for the agent
    :return: the scaling factor
    """
    scaling_factor = 10.0 ** (len(str(money_endowment)) - 1)
    return scaling_factor


def generate_good_endowments(nb_goods: int, nb_agents: int, base_amount: int, uniform_lower_bound_factor: int, uniform_upper_bound_factor: int) -> List[List[int]]:
    """
    Compute good endowments per agent. That is, a matrix of shape (nb_agents, nb_goods).

    :param nb_goods: the number of goods.
    :param nb_agents: the number of agents.
    :param base_amount: the base amount of instances per good
    :param uniform_lower_bound_factor: the lower bound of the uniform distribution for the sampling of the good instance number.
    :param uniform_upper_bound_factor: the upper bound of the uniform distribution for the sampling of the good instance number.
    :return: the endowments matrix.
    """
    # sample good instances
    instances_per_good = _sample_good_instances(nb_agents, nb_goods, base_amount,
                                                uniform_lower_bound_factor, uniform_upper_bound_factor)
    # each agent receives at least two good
    endowments = [[base_amount] * nb_goods for _ in range(nb_agents)]
    # randomly assign additional goods to create differences
    for good_id in range(nb_goods):
        for _ in range(instances_per_good[good_id] - (base_amount * nb_agents)):
            agent_id = random.randint(0, nb_agents - 1)
            endowments[agent_id][good_id] += 1
    return endowments


def generate_utility_params(nb_agents: int, nb_goods: int, scaling_factor: float) -> List[List[float]]:
    """
    Compute the preference matrix. That is, a generic element e_ij is the utility of good j for agent i.

    :param nb_agents: the number of agents.
    :param nb_goods: the number of goods.
    :param scaling_factor: a scaling factor for all the utility params generated.
    :return: the preference matrix.
    """
    utility_params = _sample_utility_function_params(nb_goods, nb_agents, scaling_factor)
    return utility_params


def _sample_utility_function_params(nb_goods: int, nb_agents: int, scaling_factor: float) -> List[List[float]]:
    """
    Sample utility function params for each agent.

    :param nb_goods: the number of goods
    :param nb_agents: the number of agents
    :param scaling_factor: a scaling factor for all the utility params generated.
    :return: a matrix with utility function params for each agent
    """
    decimals = 4 if nb_goods < 100 else 8
    utility_function_params = []
    for i in range(nb_agents):
        random_integers = [random.randint(1, 101) for _ in range(nb_goods)]
        total = sum(random_integers)
        normalized_fractions = [round(i / float(total), decimals) for i in random_integers]
        if not sum(normalized_fractions) == 1.0:
            normalized_fractions[-1] = round(1.0 - sum(normalized_fractions[0:-1]), decimals)
        utility_function_params.append(normalized_fractions)

    # scale the utility params
    for i in range(len(utility_function_params)):
        for j in range(len(utility_function_params[i])):
            utility_function_params[i][j] *= scaling_factor

    return utility_function_params


def _sample_good_instances(nb_agents: int, nb_goods: int, base_amount: int,
                           uniform_lower_bound_factor: int, uniform_upper_bound_factor: int) -> List[int]:
    """
    Sample the number of instances for a good.

    :param nb_agents: the number of agents
    :param nb_goods: the number of goods
    :param base_amount: the base amount of instances per good
    :param uniform_lower_bound_factor: the lower bound factor of a uniform distribution
    :param uniform_upper_bound_factor: the upper bound factor of a uniform distribution
    :return: the number of instances I sampled.
    """
    a = base_amount * nb_agents + nb_agents * uniform_lower_bound_factor
    b = base_amount * nb_agents + nb_agents * uniform_upper_bound_factor
    # Return random integer in range [a, b]
    nb_instances = [round(np.random.uniform(a, b)) for _ in range(nb_goods)]
    return nb_instances


def generate_money_endowments(nb_agents: int, money_endowment: int) -> List[int]:
    """
    Compute the initial money amounts for each agent.

    :param nb_agents: number of agents.
    :param money_endowment: money endowment per agent.
    :return: the list of initial money amounts.
    """
    return [money_endowment] * nb_agents


def generate_equilibrium_prices_and_holdings(endowments: List[List[int]], utility_function_params: List[List[float]], money_endowment: int, scaling_factor: float, quantity_shift: int = QUANTITY_SHIFT) -> Tuple[List[float], List[List[float]], List[float]]:
    """
    Compute the competitive equilibrium prices and allocation.

    :param endowments: endowments of the agents
    :param utility_function_params: utility function params of the agents (already scaled)
    :param money_endowment: money endowment per agent.
    :param scaling_factor: a scaling factor for all the utility params generated.
    :param quantity_shift: a factor to shift the quantities in the utility function (to ensure the natural logarithm can be used on the entire range of quantities)
    :return: the lists of equilibrium prices, equilibrium good holdings and equilibrium money holdings
    """
    endowments_a = np.array(endowments, dtype=np.int)
    scaled_utility_function_params_a = np.array(utility_function_params, dtype=np.float)  # note, they are already scaled
    endowments_by_good = np.sum(endowments_a, axis=0)
    scaled_params_by_good = np.sum(scaled_utility_function_params_a, axis=0)
    eq_prices = np.divide(scaled_params_by_good, quantity_shift * len(endowments) + endowments_by_good)
    eq_good_holdings = np.divide(scaled_utility_function_params_a, eq_prices) - quantity_shift
    eq_money_holdings = np.transpose(np.dot(eq_prices, np.transpose(endowments_a + quantity_shift))) + money_endowment - scaling_factor
    return eq_prices.tolist(), eq_good_holdings.tolist(), eq_money_holdings.tolist()

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

import collections
import math
import random
from typing import Dict, List, Tuple, cast

import numpy as np

from web3 import Web3  # pylint: disable=wrong-import-order

from aea.mail.base import Address

QUANTITY_SHIFT = 1  # Any non-negative integer is fine.
DEFAULT_CURRENCY_ID_TO_NAME = {"0": "FET"}


def generate_currency_id_to_name() -> Dict[str, str]:
    """
    Generate ids for currencies.

    :return: a dictionary mapping currency' ids to names.
    """
    return DEFAULT_CURRENCY_ID_TO_NAME


def generate_good_id_to_name(nb_goods: int) -> Dict[str, str]:
    """
    Generate ids for things.

    :param nb_goods: the number of things.
    :return: a dictionary mapping goods' ids to names.
    """
    max_number_of_digits = math.ceil(math.log10(nb_goods))
    string_format = "tac_good_{:0" + str(max_number_of_digits) + "}"
    return {str(i + 1): string_format.format(i + 1) for i in range(nb_goods)}


def determine_scaling_factor(money_endowment: int) -> float:
    """
    Compute the scaling factor based on the money amount.

    :param money_endowment: the endowment of money for the agent
    :return: the scaling factor
    """
    scaling_factor = 10.0 ** (len(str(money_endowment)) - 1)
    return scaling_factor


def generate_good_endowments(
    agent_addresses: List[str],
    good_ids: List[str],
    base_amount: int,
    uniform_lower_bound_factor: int,
    uniform_upper_bound_factor: int,
) -> Dict[str, Dict[str, int]]:
    """
    Compute good endowments per agent. That is, a matrix of shape (nb_agents, nb_goods).

    :param agent_addresses: the addresses of the agents
    :param good_ids: the list of good ids
    :param base_amount: the base amount of instances per good
    :param uniform_lower_bound_factor: the lower bound of the uniform distribution for the sampling of the good instance number.
    :param uniform_upper_bound_factor: the upper bound of the uniform distribution for the sampling of the good instance number.
    :return: the endowments matrix.
    """
    # sample good instances
    nb_agents = len(agent_addresses)
    instances_per_good = _sample_good_instances(
        nb_agents,
        good_ids,
        base_amount,
        uniform_lower_bound_factor,
        uniform_upper_bound_factor,
    )
    # each agent receives at least base amount of each good
    base_assignment = {good_id: base_amount for good_id in good_ids}
    endowments = {agent_addr: base_assignment for agent_addr in agent_addresses}
    # randomly assign additional goods to create differences
    for good_id in good_ids:
        for _ in range(instances_per_good[good_id] - (base_amount * nb_agents)):
            idx = random.randint(0, nb_agents - 1)  # nosec
            agent_addr = agent_addresses[idx]
            endowments[agent_addr][good_id] += 1
    return endowments


def generate_utility_params(
    agent_addresses: List[str], good_ids: List[str], scaling_factor: float
) -> Dict[str, Dict[str, float]]:
    """
    Compute the preference matrix. That is, a generic element e_ij is the utility of good j for agent i.

    :param agent_addresses: the agent addresses
    :param good_ids: the list of good ids
    :param scaling_factor: a scaling factor for all the utility params generated.
    :return: the preference matrix.
    """
    decimals = 4 if len(good_ids) < 100 else 8
    utility_function_params = {}  # type: Dict[str, Dict[str, float]]
    for agent_addr in agent_addresses:
        random_integers = [
            random.randint(1, 101) for _ in range(len(good_ids))  # nosec
        ]
        total = sum(random_integers)
        normalized_fractions = [
            round(i / float(total), decimals) for i in random_integers
        ]
        if not sum(normalized_fractions) == 1.0:
            normalized_fractions[-1] = round(
                1.0 - sum(normalized_fractions[0:-1]), decimals
            )
        # scale the utility params
        params = {
            good_id: param * scaling_factor
            for good_id, param in zip(good_ids, normalized_fractions)
        }
        utility_function_params[agent_addr] = params

    return utility_function_params


def _sample_good_instances(
    nb_agents: int,
    good_ids: List[str],
    base_amount: int,
    uniform_lower_bound_factor: int,
    uniform_upper_bound_factor: int,
) -> Dict[str, int]:
    """
    Sample the number of instances for a good.

    :param nb_agents: the number of agents
    :param good_ids: the good ids
    :param base_amount: the base amount of instances per good
    :param uniform_lower_bound_factor: the lower bound factor of a uniform distribution
    :param uniform_upper_bound_factor: the upper bound factor of a uniform distribution
    :return: the number of instances I sampled.
    """
    a = base_amount * nb_agents + nb_agents * uniform_lower_bound_factor
    b = base_amount * nb_agents + nb_agents * uniform_upper_bound_factor
    # Return random integer in range [a, b]
    nb_instances = {good_id: round(np.random.uniform(a, b)) for good_id in good_ids}
    return nb_instances


def generate_currency_endowments(
    agent_addresses: List[str], currency_ids: List[str], money_endowment: int
) -> Dict[str, Dict[str, int]]:
    """
    Compute the initial money amounts for each agent.

    :param agent_addresses: addresses of the agents.
    :param currency_ids: the currency ids.
    :param money_endowment: money endowment per agent.
    :return: the nested dict of currency endowments
    """
    currency_endowment = {currency_id: money_endowment for currency_id in currency_ids}
    return {agent_addr: currency_endowment for agent_addr in agent_addresses}


def generate_exchange_params(
    agent_addresses: List[str], currency_ids: List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute the exchange parameters for each agent.

    :param agent_addresses: addresses of the agents.
    :param currency_ids: the currency ids.
    :return: the nested dict of currency endowments
    """
    exchange_params = {currency_id: 1.0 for currency_id in currency_ids}
    return {agent_addr: exchange_params for agent_addr in agent_addresses}


def generate_equilibrium_prices_and_holdings(
    agent_addr_to_good_endowments: Dict[str, Dict[str, int]],
    agent_addr_to_utility_params: Dict[str, Dict[str, float]],
    agent_addr_to_currency_endowments: Dict[str, Dict[str, int]],
    agent_addr_to_exchange_params: Dict[str, Dict[str, float]],
    scaling_factor: float,
    quantity_shift: int = QUANTITY_SHIFT,
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, float]]:
    """
    Compute the competitive equilibrium prices and allocation.

    :param agent_addr_to_good_endowments: endowments of the agents
    :param agent_addr_to_utility_params: utility function params of the agents (already scaled)
    :param agent_addr_to_currency_endowments: money endowment per agent.
    :param agent_addr_to_exchange_params: exchange params per agent.
    :param scaling_factor: a scaling factor for all the utility params generated.
    :param quantity_shift: a factor to shift the quantities in the utility function (to ensure the natural logarithm can be used on the entire range of quantities)
    :return: the lists of equilibrium prices, equilibrium good holdings and equilibrium money holdings
    """
    # create ordered lists
    agent_addresses = []  # type: List[str]
    good_ids = []  # type: List[str]
    good_ids_to_idx = {}  # type: Dict[str, int]
    good_endowments_l = []  # type: List[List[int]]
    utility_params_l = []  # type: List[List[float]]
    currency_endowment_l = []  # type: List[int]
    # exchange_params_l = []  # type: List[float]
    count = 0
    for agent_addr, good_endowment in agent_addr_to_good_endowments.items():
        agent_addresses.append(agent_addr)
        assert (
            len(agent_addr_to_currency_endowments[agent_addr].values()) == 1
        ), "Cannot have more than one currency."
        currency_endowment_l.append(
            list(agent_addr_to_currency_endowments[agent_addr].values())[0]
        )
        assert len(good_endowment.keys()) == len(
            agent_addr_to_utility_params[agent_addr].keys()
        ), "Good endowments and utility params inconsistent."
        temp_g_e = [0] * len(good_endowment.keys())
        temp_u_p = [0.0] * len(agent_addr_to_utility_params[agent_addr].keys())
        idx = 0
        for good_id, quantity in good_endowment.items():
            if count == 0:
                good_ids.append(good_id)
                good_ids_to_idx[good_id] = idx
                idx += 1
            temp_g_e[good_ids_to_idx[good_id]] = quantity
            temp_u_p[good_ids_to_idx[good_id]] = agent_addr_to_utility_params[
                agent_addr
            ][good_id]
        count += 1
        good_endowments_l.append(temp_g_e)
        utility_params_l.append(temp_u_p)

    # maths
    endowments_a = np.array(good_endowments_l, dtype=np.int)
    scaled_utility_params_a = np.array(
        utility_params_l, dtype=np.float
    )  # note, they are already scaled
    endowments_by_good = np.sum(endowments_a, axis=0)
    scaled_params_by_good = np.sum(scaled_utility_params_a, axis=0)
    eq_prices = np.divide(
        scaled_params_by_good,
        quantity_shift * len(agent_addresses) + endowments_by_good,
    )
    eq_good_holdings = np.divide(scaled_utility_params_a, eq_prices) - quantity_shift
    eq_currency_holdings = (
        np.transpose(np.dot(eq_prices, np.transpose(endowments_a + quantity_shift)))
        + currency_endowment_l
        - scaling_factor
    )

    # back to dicts
    eq_prices_dict = {
        good_id: cast(float, eq_price)
        for good_id, eq_price in zip(good_ids, eq_prices.tolist())
    }
    eq_good_holdings_dict = {
        agent_addr: {good_id: cast(float, v) for good_id, v in zip(good_ids, egh)}
        for agent_addr, egh in zip(agent_addresses, eq_good_holdings.tolist())
    }
    eq_currency_holdings_dict = {
        agent_addr: cast(float, eq_currency_holding)
        for agent_addr, eq_currency_holding in zip(
            agent_addresses, eq_currency_holdings.tolist()
        )
    }
    return eq_prices_dict, eq_good_holdings_dict, eq_currency_holdings_dict


def _get_hash(
    tx_sender_addr: Address,
    tx_counterparty_addr: Address,
    good_ids: List[int],
    sender_supplied_quantities: List[int],
    counterparty_supplied_quantities: List[int],
    tx_amount: int,
    tx_nonce: int,
) -> bytes:
    """
    Generate a hash from transaction information.

    :param tx_sender_addr: the sender address
    :param tx_counterparty_addr: the counterparty address
    :param good_ids: the list of good ids
    :param sender_supplied_quantities: the quantities supplied by the sender (must all be positive)
    :param counterparty_supplied_quantities: the quantities supplied by the counterparty (must all be positive)
    :param tx_amount: the amount of the transaction
    :param tx_nonce: the nonce of the transaction
    :return: the hash
    """
    aggregate_hash = Web3.keccak(
        b"".join(
            [
                good_ids[0].to_bytes(32, "big"),
                sender_supplied_quantities[0].to_bytes(32, "big"),
                counterparty_supplied_quantities[0].to_bytes(32, "big"),
            ]
        )
    )
    for idx, good_id in enumerate(good_ids):
        if not idx == 0:
            aggregate_hash = Web3.keccak(
                b"".join(
                    [
                        aggregate_hash,
                        good_id.to_bytes(32, "big"),
                        sender_supplied_quantities[idx].to_bytes(32, "big"),
                        counterparty_supplied_quantities[idx].to_bytes(32, "big"),
                    ]
                )
            )

    m_list = []  # type: List[bytes]
    m_list.append(tx_sender_addr.encode("utf-8"))
    m_list.append(tx_counterparty_addr.encode("utf-8"))
    m_list.append(aggregate_hash)
    m_list.append(tx_amount.to_bytes(32, "big"))
    m_list.append(tx_nonce.to_bytes(32, "big"))
    return Web3.keccak(b"".join(m_list))


def tx_hash_from_values(
    tx_sender_addr: str,
    tx_counterparty_addr: str,
    tx_quantities_by_good_id: Dict[str, int],
    tx_amount_by_currency_id: Dict[str, int],
    tx_nonce: int,
) -> bytes:
    """
    Get the hash for a transaction based on the transaction message.

    :param tx_message: the transaction message
    :return: the hash
    """
    _tx_quantities_by_good_id = {
        int(good_id): quantity for good_id, quantity in tx_quantities_by_good_id.items()
    }  # type: Dict[int, int]
    ordered = collections.OrderedDict(sorted(_tx_quantities_by_good_id.items()))
    good_uids = []  # type: List[int]
    sender_supplied_quantities = []  # type: List[int]
    counterparty_supplied_quantities = []  # type: List[int]
    for good_uid, quantity in ordered.items():
        good_uids.append(good_uid)
        if quantity >= 0:
            sender_supplied_quantities.append(quantity)
            counterparty_supplied_quantities.append(0)
        else:
            sender_supplied_quantities.append(0)
            counterparty_supplied_quantities.append(-quantity)
    assert len(tx_amount_by_currency_id) == 1
    for amount in tx_amount_by_currency_id.values():
        tx_amount = amount if amount >= 0 else 0
    tx_hash = _get_hash(
        tx_sender_addr=tx_sender_addr,
        tx_counterparty_addr=tx_counterparty_addr,
        good_ids=good_uids,
        sender_supplied_quantities=sender_supplied_quantities,
        counterparty_supplied_quantities=counterparty_supplied_quantities,
        tx_amount=tx_amount,
        tx_nonce=tx_nonce,
    )
    return tx_hash

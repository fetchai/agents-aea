# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""Preference representation helpers."""

import math
from typing import Dict

from aea.exceptions import enforce


def logarithmic_utility(
    utility_params_by_good_id: Dict[str, float],
    quantities_by_good_id: Dict[str, int],
    quantity_shift: int = 100,
) -> float:
    """
    Compute agent's utility given her utility function params and a good bundle.

    :param utility_params_by_good_id: utility params by good identifier
    :param quantities_by_good_id: quantities by good identifier
    :param quantity_shift: a non-negative factor to shift the quantities in the utility function (to ensure the natural logarithm can be used on the entire range of quantities)
    :return: utility value
    """
    enforce(
        quantity_shift >= 0,
        "The quantity_shift argument must be a non-negative integer.",
    )

    goodwise_utility = [
        utility_params_by_good_id[good_id] * math.log(quantity + quantity_shift)
        if quantity + quantity_shift > 0
        else -10000
        for good_id, quantity in quantities_by_good_id.items()
    ]
    return sum(goodwise_utility)


def linear_utility(
    exchange_params_by_currency_id: Dict[str, float],
    balance_by_currency_id: Dict[str, int],
) -> float:
    """
    Compute agent's utility given her utility function params and a good bundle.

    :param exchange_params_by_currency_id: exchange params by currency
    :param balance_by_currency_id: balance by currency
    :return: utility value
    """
    money_utility = [
        exchange_params_by_currency_id[currency_id] * balance
        for currency_id, balance in balance_by_currency_id.items()
    ]
    return sum(money_utility)

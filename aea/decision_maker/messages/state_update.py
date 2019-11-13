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

"""The state update message module."""

from enum import Enum
from typing import cast, Dict, Optional, Union

from aea.protocols.base import Message

TransactionId = str
Address = str

Currencies = Dict[str, int]  # a map from identifier to quantity
Goods = Dict[str, int]   # a map from identifier to quantity
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity


class StateUpdateMessage(Message):
    """The state update message class."""

    protocol_id = "internal"

    class Performative(Enum):
        """State update performative."""

        RESET = "reset"
        APPLY = "apply"

    def __init__(self, performative: Union[str, Performative],
                 amount_by_currency_pbk: Currencies,
                 quantities_by_good_pbk: Goods,
                 utility_params: Optional[UtilityParams] = None,
                 exchange_params: Optional[ExchangeParams] = None,
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param amount_by_currency_pbk: the amounts of currencies.
        :param quantities_by_good_pbk: the quantities of goods.
        :param utility_params: the utility params.
        :param exchange_params: the exchange params.
        """
        super().__init__(performative=performative,
                         amount_by_currency_pbk=amount_by_currency_pbk,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         utility_params=utility_params,
                         exchange_params=exchange_params,
                         **kwargs)
        assert self.check_consistency(), "StateUpdateMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert self.is_set("performative")
            performative = self.get("performative")
            assert self.is_set("amount_by_currency_pbk")
            amount_by_currency_pbk = self.get("amount_by_currency_pbk")
            amount_by_currency_pbk = cast(Currencies, amount_by_currency_pbk)
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            quantities_by_good_pbk = cast(Goods, quantities_by_good_pbk)
            if performative == self.Performative.RESET:
                assert self.is_set("exchange_params")
                exchange_params = self.get("exchange_params")
                exchange_params = cast(ExchangeParams, exchange_params)
                assert amount_by_currency_pbk.keys() == exchange_params.keys()
                assert self.is_set("utility_params")
                utility_params = self.get("utility_params")
                utility_params = cast(UtilityParams, utility_params)
                assert quantities_by_good_pbk.keys() == utility_params.keys()
        except (AssertionError, KeyError):
            return False
        return True

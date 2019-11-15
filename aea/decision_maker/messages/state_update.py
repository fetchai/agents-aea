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

        INITIALIZE = "initialize"
        APPLY = "apply"

    def __init__(self, performative: Union[str, Performative],
                 amount_by_currency: Currencies,
                 quantities_by_good_pbk: Goods,
                 exchange_params_by_currency: Optional[ExchangeParams] = None,
                 utility_params_by_good_pbk: Optional[UtilityParams] = None,
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param amount_by_currency: the amounts of currencies.
        :param quantities_by_good_pbk: the quantities of goods.
        :param exchange_params_by_currency: the exchange params.
        :param utility_params_by_good_pbk: the utility params.
        """
        super().__init__(performative=performative,
                         amount_by_currency=amount_by_currency,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         exchange_params_by_currency=exchange_params_by_currency,
                         utility_params_by_good_pbk=utility_params_by_good_pbk,
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
            assert self.is_set("amount_by_currency")
            amount_by_currency = self.get("amount_by_currency")
            amount_by_currency = cast(Currencies, amount_by_currency)
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            quantities_by_good_pbk = cast(Goods, quantities_by_good_pbk)
            if performative == self.Performative.INITIALIZE:
                assert self.is_set("exchange_params_by_currency")
                exchange_params_by_currency = self.get("exchange_params_by_currency")
                exchange_params_by_currency = cast(ExchangeParams, exchange_params_by_currency)
                assert amount_by_currency.keys() == exchange_params_by_currency.keys()
                assert self.is_set("utility_params_by_good_pbk")
                utility_params_by_good_pbk = self.get("utility_params_by_good_pbk")
                utility_params_by_good_pbk = cast(UtilityParams, utility_params_by_good_pbk)
                assert quantities_by_good_pbk.keys() == utility_params_by_good_pbk.keys()
            elif performative == self.Performative.APPLY:
                assert self.get("exchange_params_by_currency") is None
                assert self.get("utility_params_by_good_pbk") is None
        except (AssertionError, KeyError):
            return False
        return True

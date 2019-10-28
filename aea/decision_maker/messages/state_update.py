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

from typing import Dict, cast

from aea.protocols.base import Message

TransactionId = str
Address = str

CurrencyEndowment = Dict[str, float]  # a map from identifier to quantity
GoodEndowment = Dict[str, int]   # a map from identifier to quantity
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity


class StateUpdateMessage(Message):
    """The transaction message class."""

    def __init__(self, currency_endowment: CurrencyEndowment,
                 good_endowment: GoodEndowment,
                 utility_params: UtilityParams,
                 exchange_params: ExchangeParams,
                 **kwargs):
        """
        Instantiate transaction message.

        :param currency_endowment: the currency endowment.
        :param good_endowment: the good endowment.
        :param utility_params: the utility params.
        :param exchange_params: the exchange params.
        """
        super().__init__(currency_endowment=currency_endowment,
                         good_endowment=good_endowment,
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
            assert self.is_set("currency_endowment")
            assert self.is_set("good_endowment")
            assert self.is_set("utility_params")
            assert self.is_set("exchange_params")
            currency_endowment = self.get("currency_endowment")
            currency_endowment = cast(CurrencyEndowment, currency_endowment)
            exchange_params = self.get("exchange_params")
            exchange_params = cast(ExchangeParams, exchange_params)
            assert currency_endowment.keys() == exchange_params.keys()
            good_endowment = self.get("good_endowment")
            good_endowment = cast(GoodEndowment, good_endowment)
            utility_params = self.get("utility_params")
            utility_params = cast(UtilityParams, utility_params)
            assert good_endowment.keys() == utility_params.keys()
        except (AssertionError, KeyError):
            return False
        return True

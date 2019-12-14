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
from typing import cast, Dict, Optional

from aea.decision_maker.messages.base import InternalMessage

TransactionId = str

Currencies = Dict[str, int]  # a map from identifier to quantity
Goods = Dict[str, int]   # a map from identifier to quantity
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity


class StateUpdateMessage(InternalMessage):
    """The state update message class."""

    class Performative(Enum):
        """State update performative."""

        INITIALIZE = "initialize"
        APPLY = "apply"

    def __init__(self, performative: Performative,
                 amount_by_currency: Currencies,
                 quantities_by_good_pbk: Goods,
                 exchange_params_by_currency: Optional[ExchangeParams] = None,
                 utility_params_by_good_pbk: Optional[UtilityParams] = None,
                 tx_fee: Optional[int] = None,
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param amount_by_currency: the amounts of currencies.
        :param quantities_by_good_pbk: the quantities of goods.
        :param exchange_params_by_currency: the exchange params.
        :param utility_params_by_good_pbk: the utility params.
        :param tx_fee: the tx fee.
        """
        if performative == self.Performative.INITIALIZE:
            super().__init__(performative=performative,
                             amount_by_currency=amount_by_currency,
                             quantities_by_good_pbk=quantities_by_good_pbk,
                             exchange_params_by_currency=exchange_params_by_currency,
                             utility_params_by_good_pbk=utility_params_by_good_pbk,
                             tx_fee=tx_fee,
                             **kwargs)
        else:
            super().__init__(performative=performative,
                             amount_by_currency=amount_by_currency,
                             quantities_by_good_pbk=quantities_by_good_pbk,
                             **kwargs)
        assert self.check_consistency(), "StateUpdateMessage initialization inconsistent."

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "Performative is not set."
        return StateUpdateMessage.Performative(self.get('performative'))

    @property
    def amount_by_currency(self) -> Currencies:
        """Get the amount by currency."""
        assert self.is_set("amount_by_currency")
        return cast(Currencies, self.get("amount_by_currency"))

    @property
    def quantities_by_good_pbk(self) -> Goods:
        """Get he quantities by good public keys."""
        assert self.is_set("quantities_by_good_pbk"), "quantities_by_good_pbk is not set."
        return cast(Goods, self.get("quantities_by_good_pbk"))

    @property
    def exchange_params_by_currency(self) -> ExchangeParams:
        """Get the exchange parameters by currency from the message."""
        assert self.is_set("exchange_params_by_currency")
        return cast(ExchangeParams, self.get("exchange_params_by_currency"))

    @property
    def utility_params_by_good_pbk(self) -> UtilityParams:
        """Get the utility parameters by good public key."""
        assert self.is_set("utility_params_by_good_pbk")
        return cast(UtilityParams, self.get("utility_params_by_good_pbk"))

    @property
    def tx_fee(self) -> int:
        """Get the transaction fee."""
        assert self.is_set("tx_fee")
        return cast(int, self.get("tx_fee"))

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert self.performative in StateUpdateMessage.Performative, "Invalide performative."
            isinstance(self.amount_by_currency, dict)
            for key, int_value in self.amount_by_currency.items():
                isinstance(key, str)
                isinstance(int_value, int)
            isinstance(self.quantities_by_good_pbk, dict)
            for key, int_value in self.quantities_by_good_pbk.items():
                isinstance(key, str)
                isinstance(int_value, int)
            if self.performative == self.Performative.INITIALIZE:
                isinstance(self.exchange_params_by_currency, dict)
                for key, float_value in self.exchange_params_by_currency.items():
                    isinstance(key, str)
                    isinstance(float_value, float)
                assert self.amount_by_currency.keys() == self.exchange_params_by_currency.keys()
                isinstance(self.utility_params_by_good_pbk, dict)
                for key, float_value in self.utility_params_by_good_pbk.items():
                    isinstance(key, str)
                    isinstance(float_value, float)
                assert self.quantities_by_good_pbk.keys() == self.utility_params_by_good_pbk.keys()
                assert self.quantities_by_good_pbk.keys() == self.utility_params_by_good_pbk.keys()
                isinstance(self.tx_fee, int)
                assert len(self.body) == 6
            elif self.performative == self.Performative.APPLY:
                assert not self.is_set("exchange_params_by_currency")
                assert not self.is_set("utility_params_by_good_pbk")
                assert not self.is_set("tx_fee")
                assert len(self.body) == 3
        except (AssertionError, KeyError):
            return False
        return True

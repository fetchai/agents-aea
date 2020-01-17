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

"""This module contains the strategy class."""

from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.skills.base import SharedClass

DEFAULT_COUNTRY = "UK"
SEARCH_TERM = "country"
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = False


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop("country", DEFAULT_COUNTRY)
        self._max_row_price = kwargs.pop("max_row_price", DEFAULT_MAX_ROW_PRICE)
        self.max_buyer_tx_fee = kwargs.pop("max_tx_fee", DEFAULT_MAX_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True

    def get_next_search_id(self) -> int:
        """
        Get the next search id and set the search time.

        :return: the next search id
        """
        self._search_id += 1
        return self._search_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query(
            [Constraint(SEARCH_TERM, ConstraintType("==", self._country))], model=None
        )
        return query

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (
            (proposal.values["price"] - proposal.values["seller_tx_fee"] > 0)
            and (
                proposal.values["price"]
                <= self._max_row_price * proposal.values["rows"]
            )
            and (proposal.values["currency_id"] == self._currency_id)
            and (proposal.values["ledger_id"] == self._ledger_id)
        )
        return result

    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = proposal.values["price"] + self.max_buyer_tx_fee
            ledger_id = proposal.values["ledger_id"]
            address = cast(str, self.context.agent_addresses.get(ledger_id))
            balance = self.context.ledger_apis.token_balance(ledger_id, address)
            result = balance >= payable
        else:
            result = True
        return result

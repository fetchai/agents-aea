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

import time
from typing import cast

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.skills.base import Model

DEFAULT_COUNTRY = "UK"
SEARCH_TERM = "country"
DEFAULT_SEARCH_INTERVAL = 5.0
DEFAULT_MAX_PRICE = 4000
DEFAULT_MAX_DETECTION_AGE = 60 * 60  # 1 hour
DEFAULT_NO_FINDSEARCH_INTERVAL = 5
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_IS_LEDGER_TX = True

DEFAULT_MAX_TX_FEE = 2


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop("country", DEFAULT_COUNTRY)
        self._search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        self._no_find_search_interval = kwargs.pop(
            "no_find_search_interval", DEFAULT_NO_FINDSEARCH_INTERVAL
        )
        self._max_price = kwargs.pop("max_price", DEFAULT_MAX_PRICE)
        self._max_detection_age = kwargs.pop(
            "max_detection_age", DEFAULT_MAX_DETECTION_AGE
        )
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self.max_buyer_tx_fee = kwargs.pop("max_buyer_tx_fee", DEFAULT_MAX_TX_FEE)

        super().__init__(**kwargs)

        self.is_searching = True

    @property
    def ledger_id(self) -> str:
        """Get the ledger id used."""
        return self._ledger_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query([Constraint("longitude", ConstraintType("!=", 0.0))], model=None)
        return query

    def on_submit_search(self):
        """Call when you submit a search ( to suspend searching)."""
        self.is_searching = False

    def on_search_success(self):
        """Call when search returns succesfully."""
        self.is_searching = True

    def on_search_failed(self):
        """Call when search returns with no matches."""
        self.is_searching = True

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (
            proposal.values["price"] < self._max_price
            and proposal.values["last_detection_time"]
            > int(time.time()) - self._max_detection_age
        )

        return result

    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = proposal.values["price"]
            ledger_id = proposal.values["ledger_id"]
            address = cast(str, self.context.agent_addresses.get(ledger_id))
            balance = self.context.ledger_apis.token_balance(ledger_id, address)
            result = balance >= payable
        else:
            self.context.logger.debug("Assuming it is affordable")
            result = True
        return result

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
import datetime

from aea.protocols.oef.models import Attribute, DataModel, Query, Constraint, ConstraintType
from aea.skills.base import SharedClass

DEFAULT_DATASET_ID = 'UK'
DEFAULT_SEARCH_INTERVAL = 5.0
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'None'


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """Initialize the strategy of the agent."""
        self.dataset_id = kwargs.pop('dataset_id', DEFAULT_DATASET_ID)
        self._search_interval = kwargs.pop('search_interval', DEFAULT_SEARCH_INTERVAL)
        self.max_row_price = kwargs.pop('max_row_price', DEFAULT_MAX_ROW_PRICE)
        self.max_tx_fee = kwargs.pop('max_tx_fee', DEFAULT_MAX_TX_FEE)
        self.currency_pbk = kwargs.pop('currency_pbk', DEFAULT_CURRENCY_PBK)
        self.ledger_id = kwargs.pop('ledger_id', DEFAULT_LEDGER_ID)
        super().__init__(**kwargs)
        self._oef_msg_id = 0

        self._search_id = 0
        self.is_searching = True
        self._last_search_time = datetime.datetime.now()

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
        query = Query([Constraint("dataset_id", ConstraintType("==", self.dataset_id))], model=dm)
        return query

    def is_time_to_search(self) -> bool:
        """
        Check whether it is time to search.

        :return: whether it is time to search
        """
        if not self.is_searching:
            return False
        now = datetime.datetime.now()
        diff = now - self._last_search_time
        result = diff.total_seconds() > self._search_interval
        return result

    def get_next_search_id(self) -> int:
        """
        Get the next search id and set the search time.

        :return: the next search id
        """
        self._search_id += 1
        self._last_search_time = datetime.datetime.now()
        return self._search_id

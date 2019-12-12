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

from aea.protocols.oef.models import Description, Query, Constraint, ConstraintType
from aea.skills.base import SharedClass

DEFAULT_COUNTRY = 'UK'
SEARCH_TERM = 'country'
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'None'


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop('country') if 'country' in kwargs.keys() else DEFAULT_COUNTRY
        self._max_row_price = kwargs.pop('max_row_price') if 'max_row_price' in kwargs.keys() else DEFAULT_MAX_ROW_PRICE
        self.max_buyer_tx_fee = kwargs.pop('max_tx_fee') if 'max_tx_fee' in kwargs.keys() else DEFAULT_MAX_TX_FEE
        self._currency_pbk = kwargs.pop('currency_pbk') if 'currency_pbk' in kwargs.keys() else DEFAULT_CURRENCY_PBK
        self._ledger_id = kwargs.pop('ledger_id') if 'ledger_id' in kwargs.keys() else DEFAULT_LEDGER_ID
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
        query = Query([Constraint(SEARCH_TERM, ConstraintType("==", self._country))], model=None)
        return query

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (proposal.values['price'] - proposal.values['seller_tx_fee'] > 0) and \
            (proposal.values['price'] <= self._max_row_price * proposal.values['rows']) and \
            (proposal.values['currency_pbk'] == self._currency_pbk) and \
            (proposal.values['ledger_id'] == self._ledger_id)
        return result

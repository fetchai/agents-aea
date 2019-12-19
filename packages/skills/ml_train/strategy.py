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
from typing import cast

from aea.helpers.search.models import Attribute, DataModel, Query, Constraint, ConstraintType, Description
from aea.skills.base import SharedClass

DEFAULT_DATASET_ID = 'UK'
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'None'


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """Initialize the strategy of the agent."""
        self._dataset_id = kwargs.pop('dataset_id', DEFAULT_DATASET_ID)
        self._max_unit_price = kwargs.pop('max_unit_price', DEFAULT_MAX_ROW_PRICE)
        self._max_buyer_tx_fee = kwargs.pop('max_buyer_tx_fee', DEFAULT_MAX_TX_FEE)
        self._currency_id = kwargs.pop('currency_id', DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop('ledger_id', DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop('is_ledger_tx', False)
        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True
        self._last_search_time = datetime.datetime.now()
        self._tx_id = 0

    def get_next_search_id(self) -> int:
        """
        Get the next search id and set the search time.

        :return: the next search id
        """
        self._search_id += 1
        self._last_search_time = datetime.datetime.now()
        return self._search_id

    def get_next_transition_id(self) -> str:
        """
        Get the next transaction id.

        :return: The next transaction id
        """
        self._tx_id += 1
        return "transaction_{}".format(self._tx_id)

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
        query = Query([Constraint("dataset_id", ConstraintType("==", self._dataset_id))], model=dm)
        return query

    def is_acceptable_terms(self, terms: Description) -> bool:
        """
        Check whether the terms are acceptable.

        :params terms: the terms
        :return: boolean
        """
        result = (terms.values['price'] - terms.values['seller_tx_fee'] > 0) and \
            (terms.values['price'] <= self._max_unit_price * terms.values['batch_size']) and \
            (terms.values['buyer_tx_fee'] <= self._max_buyer_tx_fee) and \
            (terms.values['currency_id'] == self._currency_id) and \
            (terms.values['ledger_id'] == self._ledger_id)
        return result

    def is_affordable_terms(self, terms: Description) -> bool:
        """
        Check whether the terms are affordable.

        :params terms: the terms
        :return: whether it is affordable
        """
        if self.is_ledger_tx:
            payable = terms.values['price'] - terms.values['seller_tx_fee'] + terms.values['buyer_tx_fee']
            ledger_id = terms.values['ledger_id']
            address = cast(str, self.context.agent_addresses.get(ledger_id))
            balance = self.context.ledger_apis.token_balance(ledger_id, address)
            result = balance >= payable
        else:
            result = True
        return result

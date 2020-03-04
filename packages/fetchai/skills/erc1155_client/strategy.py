# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 Fetch.AI Limited
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

from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.skills.base import Model

DEFAULT_MAX_PRICE = 5
DEFAULT_MAX_BUYER_TX_FEE = 2
DEFAULT_LEDGER_ID = "ethereum"
DEFAULT_IS_LEDGER_TX = True


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True
        self.search_query = kwargs.pop("search_query")

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
            [
                Constraint(
                    self.search_query["search_term"],
                    ConstraintType(
                        self.search_query["constraint_type"],
                        self.search_query["search_value"],
                    ),
                )
            ],
            model=None,
        )
        return query

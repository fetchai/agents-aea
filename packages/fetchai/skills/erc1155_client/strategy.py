# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

from aea.configurations.constants import DEFAULT_LEDGER
from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.skills.base import Model

DEFAULT_SEARCH_QUERY = {
    "search_term": "has_erc1155_contract",
    "search_value": True,
    "constraint_type": "==",
}
DEFAULT_LEDGER_ID = DEFAULT_LEDGER


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        assert all(
            [
                key in self._search_query
                for key in ["search_term", "constraint_type", "search_value"]
            ]
        ), "Invalid search query data."
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        super().__init__(**kwargs)
        self.is_searching = True

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query(
            [
                Constraint(
                    self._search_query["search_term"],
                    ConstraintType(
                        self._search_query["constraint_type"],
                        self._search_query["search_value"],
                    ),
                )
            ],
            model=None,
        )
        return query

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
from aea.helpers.search.generic import SIMPLE_SERVICE_MODEL
from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.skills.base import Model

DEFAULT_LOCATION = {"longitude": 51.5194, "latitude": 0.1270}
DEFAULT_SEARCH_QUERY = {
    "search_key": "seller_service",
    "search_value": "erc1155_contract",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0

DEFAULT_LEDGER_ID = DEFAULT_LEDGER


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = Location(location["longitude"], location["latitude"])
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)

        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        super().__init__(**kwargs)
        self.is_searching = True

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_location_and_service_query(self) -> Query:
        """
        Get the location and service query of the agent.

        :return: the query
        """
        close_to_my_service = Constraint(
            "location", ConstraintType("distance", (self._agent_location, self._radius))
        )
        service_key_filter = Constraint(
            self._search_query["search_key"],
            ConstraintType(
                self._search_query["constraint_type"],
                self._search_query["search_value"],
            ),
        )
        query = Query([close_to_my_service, service_key_filter],)
        return query

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        service_key_filter = Constraint(
            self._search_query["search_key"],
            ConstraintType(
                self._search_query["constraint_type"],
                self._search_query["search_value"],
            ),
        )
        query = Query([service_key_filter], model=SIMPLE_SERVICE_MODEL)
        return query

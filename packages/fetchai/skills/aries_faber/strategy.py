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

from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Location,
    Query,
)
from aea.skills.base import Model

DEFAULT_LOCATION = {"longitude": 51.5194, "latitude": 0.1270}
DEFAULT_SEARCH_QUERY = {
    "search_key": "intro_service",
    "search_value": "intro_alice",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0


class FaberStrategy(Model):
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

        super().__init__(**kwargs)
        self._is_searching = False

    @property
    def is_searching(self) -> bool:
        """Check if the agent is searching."""
        return self._is_searching

    @is_searching.setter
    def is_searching(self, is_searching: bool) -> None:
        """Check if the agent is searching."""
        assert isinstance(is_searching, bool), "Can only set bool on is_searching!"
        self._is_searching = is_searching

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

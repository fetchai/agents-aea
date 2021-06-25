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

"""This package contains a strategy model."""

from typing import Any

from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.skills.base import Model


DEFAULT_SEARCH_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "seller_service",
    "search_value": "generic_service",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0
DEFAULT_SHARED_STORAGE_KEY = "agents_found"


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("search_location", DEFAULT_SEARCH_LOCATION)
        self._agent_location = Location(
            latitude=location["latitude"], longitude=location["longitude"]
        )
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)
        self._shared_storage_key = kwargs.pop(
            "shared_storage_key", DEFAULT_SHARED_STORAGE_KEY
        )
        super().__init__(**kwargs)

    @property
    def shared_storage_key(self) -> str:
        """Get shared storage key."""
        return self._shared_storage_key

    def get_query(self) -> Query:
        """
        Get the location description.

        :return: a description of the agent's location
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
        query = Query([close_to_my_service, service_key_filter])
        return query

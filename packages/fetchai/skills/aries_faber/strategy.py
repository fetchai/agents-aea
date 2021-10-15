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

from typing import Any

from aea.common import Address
from aea.exceptions import enforce
from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.skills.base import Model


# Default Config
DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8021
DEFAULT_LEDGER_URL = "http://127.0.0.1:9000"

# Commands
ADMIN_COMMAND_CREATE_INVITATION = "/connections/create-invitation"
ADMIN_COMMAND_STATUS = "/status"
ADMIN_COMMAND_SCEHMAS = "/schemas"
ADMIN_COMMAND_CREDDEF = "/credential-definitions"
LEDGER_COMMAND_REGISTER_DID = "/register"

# Convenience
FABER_ACA_IDENTITY = "Faber_ACA"

# Search
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "intro_service",
    "search_value": "intro_alice",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        # config
        self._admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self._admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)
        self._ledger_url = kwargs.pop("ledger_url", DEFAULT_LEDGER_URL)

        # derived config
        self._admin_url = f"http://{self.admin_host}:{self.admin_port}"
        self._alice_aea_address = ""

        # Search
        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = Location(
            latitude=location["latitude"], longitude=location["longitude"]
        )
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)

        super().__init__(**kwargs)
        self._is_searching = False

    @property
    def admin_host(self) -> str:
        """Get the admin host."""
        return self._admin_host

    @property
    def admin_port(self) -> str:
        """Get the admin port."""
        return self._admin_port

    @property
    def ledger_url(self) -> str:
        """Get the ledger URL."""
        return self._ledger_url

    @property
    def admin_url(self) -> str:
        """Get the admin URL."""
        return self._admin_url

    @property
    def alice_aea_address(self) -> Address:
        """Get Alice's address."""
        return self._alice_aea_address

    @alice_aea_address.setter
    def alice_aea_address(self, address: Address) -> None:
        self._alice_aea_address = address

    @property
    def is_searching(self) -> bool:
        """Check if the agent is searching."""
        return self._is_searching

    @is_searching.setter
    def is_searching(self, is_searching: bool) -> None:
        """Check if the agent is searching."""
        enforce(isinstance(is_searching, bool), "Can only set bool on is_searching!")
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

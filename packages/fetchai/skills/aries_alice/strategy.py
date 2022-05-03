# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
import random
from typing import Any, Dict, List

from aea.common import Address
from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.skills.base import Model


# Search
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "intro_service",
    "search_value": "intro_alice",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0


# default configs
DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8031

# commands
ADMIN_COMMAND_RECEIVE_INVITE = "/connections/receive-invitation"
ADMIN_COMMAND_CREATE_INVITATION = "/connections/create-invitation"

# convenience
ALICE_ACA_IDENTITY = "Alice_ACA"
HTTP_COUNTERPARTY = "HTTP Server"

# search
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "intro_service", "value": "intro_alice"}
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "identity.aries.alice"}


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

        self._admin_url = f"http://{self.admin_host}:{self.admin_port}"

        self._seed = (
            kwargs.pop("seed", None,)
            or (
                "my_seed_000000000000000000000000"
                + str(random.randint(100_000, 999_999))  # nosec
            )[-32:]
        )

        # search
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_personality_data = kwargs.pop(
            "personality_data", DEFAULT_PERSONALITY_DATA
        )
        enforce(
            len(self._set_personality_data) == 2
            and "piece" in self._set_personality_data
            and "value" in self._set_personality_data,
            "personality_data must contain keys `key` and `value`",
        )
        self._set_classification = kwargs.pop("classification", DEFAULT_CLASSIFICATION)
        enforce(
            len(self._set_classification) == 2
            and "piece" in self._set_classification
            and "value" in self._set_classification,
            "classification must contain keys `key` and `value`",
        )
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._remove_service_data = {"key": self._set_service_data["key"]}
        self.is_searching = False
        # Search
        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)
        self.invitations: Dict[str, Address] = {}
        self.connections: Dict[str, Address] = {}
        self.aea_addresses: List[Address] = []

        super().__init__(**kwargs)

    @property
    def admin_host(self) -> str:
        """Get the admin host."""
        return self._admin_host

    @property
    def admin_port(self) -> str:
        """Get the admin port."""
        return self._admin_port

    @property
    def admin_url(self) -> str:
        """Get the admin URL."""
        return self._admin_url

    @property
    def seed(self) -> str:
        """Get the wallet seed."""
        return self._seed

    def get_location_and_service_query(self) -> Query:
        """
        Get the location and service query of the agent.

        :return: the query
        """
        close_to_my_service = Constraint(
            "location",
            ConstraintType(
                "distance", (self._agent_location["location"], self._radius)
            ),
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

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_register_personality_description(self) -> Description:
        """
        Get the register personality description.

        :return: a description of the personality
        """
        description = Description(
            self._set_personality_data, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_classification_description(self) -> Description:
        """
        Get the register classification description.

        :return: a description of the classification
        """
        description = Description(
            self._set_classification, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

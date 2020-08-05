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

from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location
from aea.skills.base import Model

DEFAULT_LOCATION = {"longitude": 51.5194, "latitude": 0.1270}
DEFAULT_SERVICE_DATA = {"key": "intro_service", "value": "intro_alice"}


class AliceStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(location["longitude"], location["latitude"])
        }
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        assert (
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data
        ), "service_data must contain keys `key` and `value`"
        self._remove_service_data = {"key": self._set_service_data["key"]}

        super().__init__(**kwargs)

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

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

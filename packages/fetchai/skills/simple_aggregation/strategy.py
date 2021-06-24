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

"""This package contains the strategy for the oracle aggregation skill."""

import statistics
from typing import Any, Dict, Optional, Set, Tuple

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


DEFAULT_SEARCH_RADIUS = 5.0
DEFAULT_SERVICE_ID = "aggregation"
DEFAULT_AGGREGATION_FUNCTION = "mean"
DEFAULT_SERVICE_DATA = {"key": "service", "value": "generic_aggregation_service"}
DEFAULT_QUANTITY_NAME = "quantity"
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "agent"}
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "service",
    "search_value": "generic_aggregation_service",
    "constraint_type": "==",
}
IMPLEMENTED_AGGREGATION_FUNCTIONS = {"mean", "median", "mode"}
DEFAULT_DECIMALS = 0


class AggregationStrategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """

        self._round = 0
        self._peers = set()  # type: Set[Address]
        self._observations = dict()  # type: Dict[Address, Dict[str, Any]]
        self._aggregation = None  # type: Optional[Any]

        self._quantity_name = kwargs.pop("quantity_name", DEFAULT_QUANTITY_NAME)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)
        self._aggregation_function = kwargs.pop(
            "aggregation_function", DEFAULT_AGGREGATION_FUNCTION
        )
        enforce(
            self._aggregation_function in IMPLEMENTED_AGGREGATION_FUNCTIONS,
            f"aggregation_function must be one of {IMPLEMENTED_AGGREGATION_FUNCTIONS}",
        )
        self._aggregate = getattr(statistics, self._aggregation_function)

        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)
        self._decimals = kwargs.pop("decimals", DEFAULT_DECIMALS)

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
        self._simple_service_data = {
            self._set_service_data["key"]: self._set_service_data["value"]
        }

        super().__init__(**kwargs)

        ledger_id = kwargs.pop("ledger_id", None)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id  # pragma: nocover

    @property
    def observation(self) -> Optional[Dict[str, Any]]:
        """Get latest observation"""
        my_address = self.context.agent_addresses[self._ledger_id]
        return self._observations.get(my_address, None)

    @property
    def peers(self) -> Set[str]:
        """Get registered peers."""
        return self._peers

    @property
    def quantity_name(self) -> str:
        """Get the name of the quantity to aggregate."""
        return self._quantity_name

    def add_peers(self, found_peers: Tuple[str, ...]) -> None:
        """
        Update registered peers with list found in search

        :param found_peers: the peers found
        """
        for _, peer in enumerate(found_peers):
            self._peers.add(peer)

    def add_observation(self, peer: Address, obs: Dict[str, Any]) -> None:
        """Add new observation to list of observations"""
        if peer in self._peers:
            self._observations[peer] = obs

    def make_observation(
        self, value: int, obs_time: str, source: str = "", signature: str = ""
    ) -> None:
        """Make observation of oracle value"""
        my_address = self.context.agent_addresses[self._ledger_id]
        observation = dict(
            value=value, time=obs_time, source=source, signature=signature
        )
        self.context.logger.info(f"Observation: {observation}")
        self._observations[my_address] = observation

    def aggregate_observations(self) -> None:
        """Aggregate values from all observations from myself and peers"""
        values = [float(obs["value"]) for obs in self._observations.values()]
        if len(values) == 0:  # pragma: nocover
            self.context.logger.info("No observations to aggregate")
            return
        self._aggregation = self._aggregate(values)
        aggregated_key = self.quantity_name + "_" + self._aggregation_function
        self.context.shared_state[aggregated_key] = {
            "value": int(self._aggregation),
            "decimals": self._decimals,
        }
        self.context.logger.info(f"Observations: {values}")
        self.context.logger.info(
            f"Aggregation ({self._aggregation_function}): {self._aggregation}"
        )

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

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

"""This package contains a class representing the game parameters."""

import datetime
from typing import Dict, Set

from aea.exceptions import enforce
from aea.helpers.search.models import Location
from aea.skills.base import Model

DEFAULT_LOCATION = {"longitude": 51.5194, "latitude": 0.1270}
DEFAULT_SERVICE_DATA = {"key": "tac", "value": "v1"}


class Parameters(Model):
    """This class contains the parameters of the game."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        self._min_nb_agents = kwargs.pop("min_nb_agents", 5)  # type: int
        self._money_endowment = kwargs.pop("money_endowment", 200)  # type: int
        self._nb_goods = kwargs.pop("nb_goods", 5)  # type: int
        self._tx_fee = kwargs.pop("tx_fee", 1)
        self._base_good_endowment = kwargs.pop("base_good_endowment", 2)  # type: int
        self._lower_bound_factor = kwargs.pop("lower_bound_factor", 1)  # type: int
        self._upper_bound_factor = kwargs.pop("upper_bound_factor", 1)  # type: int
        start_time = kwargs.pop("start_time", "01 01 2020  00:01")  # type: str
        self._start_time = datetime.datetime.strptime(
            start_time, "%d %m %Y %H:%M"
        )  # type: datetime.datetime
        self._registration_timeout = kwargs.pop("registration_timeout", 10)  # type: int
        self._competition_timeout = kwargs.pop("competition_timeout", 20)  # type: int
        self._inactivity_timeout = kwargs.pop("inactivity_timeout", 10)  # type: int
        self._whitelist = set(kwargs.pop("whitelist", []))  # type: Set[str]
        self._location = kwargs.pop("location", DEFAULT_LOCATION)
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._service_data) == 2
            and "key" in self._service_data
            and "value" in self._service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._version_id = self._service_data["value"]  # type: str

        self._agent_location = {
            "location": Location(
                self._location["longitude"], self._location["latitude"]
            )
        }
        self._set_service_data = self._service_data
        self._remove_service_data = {"key": self._service_data["key"]}
        self._simple_service_data = {
            self._service_data["key"]: self._service_data["value"]
        }

        super().__init__(**kwargs)
        now = datetime.datetime.now()
        if now > self.registration_start_time:
            self.context.logger.warning(
                "TAC registration start time {} is in the past!".format(
                    self.registration_start_time
                )
            )
        else:
            self.context.logger.info(
                "TAC registation start time: {}, and start time: {}, and end time: {}".format(
                    self.registration_start_time, self.start_time, self.end_time,
                )
            )

    @property
    def min_nb_agents(self) -> int:
        """Minimum number of agents required for a TAC instance."""
        return self._min_nb_agents

    @property
    def money_endowment(self) -> int:
        """Money endowment per agent for a TAC instance."""
        return self._money_endowment

    @property
    def nb_goods(self) -> int:
        """Good number for a TAC instance."""
        return self._nb_goods

    @property
    def tx_fee(self) -> int:
        """Transaction fee for a TAC instance."""
        return self._tx_fee

    @property
    def base_good_endowment(self) -> int:
        """Minimum endowment of each agent for each good."""
        return self._base_good_endowment

    @property
    def lower_bound_factor(self) -> int:
        """Lower bound of a uniform distribution."""
        return self._lower_bound_factor

    @property
    def upper_bound_factor(self) -> int:
        """Upper bound of a uniform distribution."""
        return self._upper_bound_factor

    @property
    def registration_start_time(self) -> datetime.datetime:
        """TAC registration start time."""
        return self._start_time - datetime.timedelta(seconds=self._registration_timeout)

    @property
    def start_time(self) -> datetime.datetime:
        """TAC start time."""
        return self._start_time

    @property
    def end_time(self) -> datetime.datetime:
        """TAC end time."""
        return self._start_time + datetime.timedelta(seconds=self._competition_timeout)

    @property
    def inactivity_timeout(self):
        """Timeout of agent inactivity from controller perspective (no received transactions)."""
        return self._inactivity_timeout

    @property
    def whitelist(self) -> Set[str]:
        """Whitelist of agent addresses allowed into the TAC instance."""
        return self._whitelist

    @property
    def version_id(self) -> str:
        """Version id."""
        return self._version_id

    @property
    def agent_location(self) -> Dict[str, Location]:
        """Get the agent location."""
        return self._agent_location

    @property
    def set_service_data(self) -> Dict[str, str]:
        """Get the set service data."""
        return self._set_service_data

    @property
    def remove_service_data(self) -> Dict[str, str]:
        """Get the remove service data."""
        return self._remove_service_data

    @property
    def simple_service_data(self) -> Dict[str, str]:
        """Get the simple service data."""
        return self._simple_service_data

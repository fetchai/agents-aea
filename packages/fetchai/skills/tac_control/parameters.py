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
from typing import Any, Dict, List, Optional, Set

from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.search.models import Location
from aea.skills.base import Model

from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as CONTRACT_ID
from packages.fetchai.skills.tac_control.helpers import (
    generate_currency_id_to_name,
    generate_good_id_to_name,
)


DEFAULT_MIN_NB_AGENTS = 2
DEFAULT_MONEY_ENDOWMENT = 200
DEFAULT_NB_GOODS = 9  # ERC1155 vyper contract only accepts 10 tokens per mint/create
DEFAULT_NB_CURRENCIES = 1
DEFAULT_TX_FEE = 1
DEFAULT_GAS = 5000000
DEFAULT_BASE_GOOD_ENDOWMENT = 2
DEFAULT_LOWER_BOUND_FACTOR = 1
DEFAULT_UPPER_BOUND_FACTOR = 1
DEFAULT_REGISTRATION_START_TIME = "01 01 2020  00:01"
DEFAULT_REGISTRATION_TIMEOUT = 60
DEFAULT_ITEM_SETUP_TIMEOUT = 60
DEFAULT_COMPETITION_TIMEOUT = 300
DEFAULT_INACTIVITY_TIMEOUT = 30
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "tac", "value": "v1"}
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "service"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "tac.controller"}


class Parameters(Model):
    """This class contains the parameters of the game."""

    def __init__(self, **kwargs: Any) -> None:
        """Instantiate the parameter class."""
        ledger_id = kwargs.pop("ledger_id", None)
        self._contract_address = kwargs.pop(
            "contract_address", None
        )  # type: Optional[str]
        self._good_ids = kwargs.pop("good_ids", [])  # type: List[int]
        self._currency_ids = kwargs.pop("currency_ids", [])  # type: List[int]
        self._min_nb_agents = kwargs.pop(
            "min_nb_agents", DEFAULT_MIN_NB_AGENTS
        )  # type: int
        self._money_endowment = kwargs.pop(
            "money_endowment", DEFAULT_MONEY_ENDOWMENT
        )  # type: int
        self._nb_goods = kwargs.pop("nb_goods", DEFAULT_NB_GOODS)  # type: int
        self._nb_currencies = kwargs.pop(
            "nb_currencies", DEFAULT_NB_CURRENCIES
        )  # type: int
        self._tx_fee = kwargs.pop("tx_fee", DEFAULT_TX_FEE)  # type: int
        self._gas = kwargs.pop("gas", DEFAULT_GAS)  # type: int
        self._base_good_endowment = kwargs.pop(
            "base_good_endowment", DEFAULT_BASE_GOOD_ENDOWMENT
        )  # type: int
        self._lower_bound_factor = kwargs.pop(
            "lower_bound_factor", DEFAULT_LOWER_BOUND_FACTOR
        )  # type: int
        self._upper_bound_factor = kwargs.pop(
            "upper_bound_factor", DEFAULT_UPPER_BOUND_FACTOR
        )  # type: int
        registration_start_time = kwargs.pop(
            "registration_start_time", DEFAULT_REGISTRATION_START_TIME
        )  # type: str
        self._registration_start_time = datetime.datetime.strptime(
            registration_start_time, "%d %m %Y %H:%M"
        )  # type: datetime.datetime
        self._registration_timeout = kwargs.pop(
            "registration_timeout", DEFAULT_REGISTRATION_TIMEOUT
        )  # type: int
        self._item_setup_timeout = kwargs.pop(
            "item_setup_timeout", DEFAULT_ITEM_SETUP_TIMEOUT
        )  # type: int
        self._competition_timeout = kwargs.pop(
            "competition_timeout", DEFAULT_COMPETITION_TIMEOUT
        )  # type: int
        self._inactivity_timeout = kwargs.pop(
            "inactivity_timeout", DEFAULT_INACTIVITY_TIMEOUT
        )  # type: int
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
                latitude=self._location["latitude"],
                longitude=self._location["longitude"],
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
        self._set_service_data = self._service_data
        self._remove_service_data = {"key": self._service_data["key"]}
        self._simple_service_data = {
            self._service_data["key"]: self._service_data["value"]
        }

        super().__init__(**kwargs)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )
        self._contract_id = str(CONTRACT_ID)
        self._currency_id_to_name = generate_currency_id_to_name(
            self.nb_currencies, self.currency_ids
        )
        self._good_id_to_name = generate_good_id_to_name(
            self.nb_goods, self.good_ids, starting_index=1
        )
        self._registration_end_time = (
            self._registration_start_time
            + datetime.timedelta(seconds=self._registration_timeout)
        )
        self._start_time = self._registration_end_time + datetime.timedelta(
            seconds=self._item_setup_timeout
        )
        self._end_time = self._start_time + datetime.timedelta(
            seconds=self._competition_timeout
        )
        now = datetime.datetime.now()
        if now > self.registration_start_time:
            self.context.logger.warning(
                "TAC registration start time {} is in the past! Deregistering skill.".format(
                    self.registration_start_time
                )
            )
            self.context.is_active = False
        else:
            self.context.logger.info(
                "TAC registation start time: {}, and registration end time: {}, and start time: {}, and end time: {}".format(
                    self.registration_start_time,
                    self.registration_end_time,
                    self.start_time,
                    self.end_time,
                )
            )
        self._check_consistency()

    @property
    def ledger_id(self) -> str:
        """Get the ledger identifier."""
        return self._ledger_id

    @property
    def contract_address(self) -> str:
        """The contract address of an already deployed smart-contract."""
        if self._contract_address is None:
            raise AEAEnforceError("No contract address provided.")
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set contract address of an already deployed smart-contract."""
        if self._contract_address is not None:
            raise AEAEnforceError("Contract address already provided.")
        self._contract_address = contract_address

    @property
    def contract_id(self) -> str:
        """Get the contract id."""
        return self._contract_id

    @property
    def is_contract_deployed(self) -> bool:
        """Check if there is a deployed instance of the contract."""
        return self._contract_address is not None

    @property
    def good_ids(self) -> List[int]:
        """The item ids of an already deployed smart-contract."""
        return self._good_ids

    @property
    def currency_ids(self) -> List[int]:
        """The currency ids of an already deployed smart-contract."""
        return self._currency_ids

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
    def nb_currencies(self) -> int:
        """Currency number for a TAC instance."""
        return self._nb_currencies

    @property
    def currency_id_to_name(self) -> Dict[str, str]:
        """Mapping of currency ids to names"""
        return self._currency_id_to_name

    @property
    def good_id_to_name(self) -> Dict[str, str]:
        """Mapping of good ids to names."""
        return self._good_id_to_name

    @property
    def tx_fee(self) -> int:
        """Transaction fee for a TAC instance."""
        return self._tx_fee

    @property
    def gas(self) -> int:
        """Gas for TAC contract operations."""
        return self._gas

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
        return self._registration_start_time

    @property
    def registration_end_time(self) -> datetime.datetime:
        """TAC registration end time."""
        return self._registration_end_time

    @property
    def start_time(self) -> datetime.datetime:
        """TAC start time."""
        return self._start_time

    @property
    def end_time(self) -> datetime.datetime:
        """TAC end time."""
        return self._end_time

    @property
    def inactivity_timeout(self) -> int:
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
    def set_personality_data(self) -> Dict[str, str]:
        """Get the set service data."""
        return self._set_personality_data

    @property
    def set_classification(self) -> Dict[str, str]:
        """Get the set service data."""
        return self._set_classification

    @property
    def remove_service_data(self) -> Dict[str, str]:
        """Get the remove service data."""
        return self._remove_service_data

    @property
    def simple_service_data(self) -> Dict[str, str]:
        """Get the simple service data."""
        return self._simple_service_data

    def _check_consistency(self) -> None:
        """Check the parameters are consistent."""
        if self._contract_address is not None and (
            (self._good_ids is not None and len(self._good_ids) != self._nb_goods)
            or (
                self._currency_ids is not None
                and len(self._currency_ids) != self._nb_currencies
            )
        ):
            raise ValueError(
                "If the contract address is set, then good ids and currency id must be provided and consistent."
            )

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
from typing import List, Optional, Set

from aea.skills.base import Model

DEFAULT_MIN_NB_AGENTS = 5
DEFAULT_MONEY_ENDOWMENT = 200
DEFAULT_NB_GOODS = 9  # ERC1155 vyper contract only accepts 10 tokens per mint/create
DEFAULT_NB_CURRENCIES = 1
DEFAULT_TX_FEE = 1
DEFAULT_BASE_GOOD_ENDOWMENT = 2
DEFAULT_LOWER_BOUND_FACTOR = 1
DEFAULT_UPPER_BOUND_FACTOR = 1
DEFAULT_START_TIME = "01 01 2020  00:01"
DEFAULT_REGISTRATION_TIMEOUT = 60
DEFAULT_ITEM_SETUP_TIMEOUT = 60
DEFAULT_COMPETITION_TIMEOUT = 300
DEFAULT_INACTIVITY_TIMEOUT = 30
DEFAULT_VERSION = "v1"
DEFAULT_LEDGER_ID = "ethereum"


class Parameters(Model):
    """This class contains the parameters of the game."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""

        self._ledger = kwargs.pop("ledger", DEFAULT_LEDGER_ID)
        self._contract_address = kwargs.pop(
            "contract_adress", None
        )  # type: Optional[str]
        self._good_ids = kwargs.pop("good_ids", [])  # type: List[int]
        self._currency_ids = kwargs.pop("currency_ids", [])  # type: List[int]
        self._min_nb_agents = kwargs.pop(
            "min_nb_agents", DEFAULT_MIN_NB_AGENTS
        )  # type: int
        self._money_endowment = kwargs.pop(
            "money_endowment", DEFAULT_MONEY_ENDOWMENT
        )  # type: int
        self._nb_goods = DEFAULT_NB_GOODS
        self._nb_currencies = DEFAULT_NB_CURRENCIES
        self._tx_fee = kwargs.pop("tx_fee", DEFAULT_TX_FEE)
        self._base_good_endowment = kwargs.pop(
            "base_good_endowment", DEFAULT_BASE_GOOD_ENDOWMENT
        )  # type: int
        self._lower_bound_factor = kwargs.pop(
            "lower_bound_factor", DEFAULT_LOWER_BOUND_FACTOR
        )  # type: int
        self._upper_bound_factor = kwargs.pop(
            "upper_bound_factor", DEFAULT_UPPER_BOUND_FACTOR
        )  # type: int
        start_time = kwargs.pop("start_time", DEFAULT_START_TIME)  # type: str
        self._start_time = datetime.datetime.strptime(
            start_time, "%d %m %Y %H:%M"
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
        self._version_id = kwargs.pop("version_id", DEFAULT_VERSION)  # type: str
        super().__init__(**kwargs)
        now = datetime.datetime.now()
        if now > self.registration_start_time:
            self.context.logger.warning(
                "[{}]: TAC registration start time {} is in the past! Deregistering skill.".format(
                    self.context.agent_name, self.registration_start_time
                )
            )
            self.context.is_active = False
        else:
            self.context.logger.info(
                "[{}]: TAC registation start time: {}, and registration end time: {}, and start time: {}, and end time: {}".format(
                    self.context.agent_name,
                    self.registration_start_time,
                    self.registration_end_time,
                    self.start_time,
                    self.end_time,
                )
            )
        self._check_consistency()

    @property
    def ledger(self) -> str:
        """Get the ledger identifier."""
        return self._ledger

    @property
    def contract_address(self) -> str:
        """The contract address of an already deployed smart-contract."""
        assert self._contract_address is not None, "No contract address provided."
        return self._contract_address

    @property
    def is_contract_deployed(self) -> bool:
        """Check if there is a deployed instance of the contract."""
        return self._contract_address is not None

    @property
    def good_ids(self) -> List[int]:
        """The item ids of an already deployed smart-contract."""
        assert self.is_contract_deployed, "There is no deployed contract."
        assert self._good_ids != [], "No good_ids provided."
        return self._good_ids

    @property
    def currency_ids(self) -> List[int]:
        """The currency ids of an already deployed smart-contract."""
        assert self.is_contract_deployed, "There is no deployed contract."
        assert self._currency_ids != [], "No currency_ids provided."
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
        return (
            self._start_time
            - datetime.timedelta(seconds=self._item_setup_timeout)
            - datetime.timedelta(seconds=self._registration_timeout)
        )

    @property
    def registration_end_time(self) -> datetime.datetime:
        """TAC registration end time."""
        return self._start_time - datetime.timedelta(seconds=self._item_setup_timeout)

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

    def _check_consistency(self) -> None:
        """Check the parameters are consistent."""
        if self._contract_address is not None and (
            self._good_ids == []
            or self._currency_ids == []
            or len(self._good_ids) != self._nb_goods
            or len(self._currency_ids) != self._nb_currencies
        ):
            raise ValueError(
                "If the contract address is set, then good ids and currency id must be provided and consistent."
            )

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

"""This package contains a class representing the game."""
from enum import Enum
from typing import Any, Dict, List, Optional

from aea.common import Address
from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.search.models import Constraint, ConstraintType, Location, Query
from aea.skills.base import Model

from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    StateUpdateDialogue,
    TacDialogue,
)


DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SEARCH_QUERY = {
    "search_key": "tac",
    "search_value": "v1",
    "constraint_type": "==",
}
DEFAULT_SEARCH_RADIUS = 5.0


class Phase(Enum):
    """This class defines the phases of the game."""

    PRE_GAME = "pre_game"
    GAME_REGISTRATION = "game_registration"
    GAME_SETUP = "game_setup"
    GAME = "game"
    POST_GAME = "post_game"


class Configuration:
    """Class containing the game configuration of a TAC instance."""

    def __init__(
        self,
        version_id: str,
        fee_by_currency_id: Dict[str, int],
        agent_addr_to_name: Dict[Address, str],
        good_id_to_name: Dict[str, str],
        controller_addr: Address,
    ):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param fee_by_currency_id: the fee for a transaction by currency id.
        :param agent_addr_to_name: a dictionary mapping agent addresses to agent names (as strings).
        :param good_id_to_name: a dictionary mapping good ids to good names (as strings).
        :param controller_addr: the address of the controller
        """
        self._version_id = version_id
        self._nb_agents = len(agent_addr_to_name)
        self._nb_goods = len(good_id_to_name)
        self._fee_by_currency_id = fee_by_currency_id
        self._agent_addr_to_name = agent_addr_to_name
        self._good_id_to_name = good_id_to_name
        self._controller_addr = controller_addr

        self._check_consistency()

    @property
    def version_id(self) -> str:
        """Agent number of a TAC instance."""
        return self._version_id

    @property
    def nb_agents(self) -> int:
        """Agent number of a TAC instance."""
        return self._nb_agents

    @property
    def nb_goods(self) -> int:
        """Good number of a TAC instance."""
        return self._nb_goods

    @property
    def tx_fee(self) -> int:
        """Transaction fee for the TAC instance."""
        enforce(
            len(self._fee_by_currency_id) == 1, "More than one currency id present!"
        )
        value = next(iter(self._fee_by_currency_id.values()))
        return value

    @property
    def fee_by_currency_id(self) -> Dict[str, int]:
        """Transaction fee for the TAC instance."""
        return self._fee_by_currency_id

    @property
    def agent_addr_to_name(self) -> Dict[Address, str]:
        """Map agent addresses to names."""
        return self._agent_addr_to_name

    @property
    def good_id_to_name(self) -> Dict[Address, str]:
        """Map good ids to names."""
        return self._good_id_to_name

    @property
    def agent_addresses(self) -> List[Address]:
        """List of agent addresses."""
        return list(self._agent_addr_to_name.keys())

    @property
    def agent_names(self) -> List[str]:
        """List of agent names."""
        return list(self._agent_addr_to_name.values())

    @property
    def good_ids(self) -> List[Address]:
        """List of good ids."""
        return list(self._good_id_to_name.keys())

    @property
    def good_names(self) -> List[str]:
        """List of good names."""
        return list(self._good_id_to_name.values())

    @property
    def controller_addr(self) -> str:
        """Get the controller address."""
        return self._controller_addr

    def _check_consistency(self) -> None:
        """Check the consistency of the game configuration."""
        enforce(self.version_id is not None, "A version id must be set.")
        enforce(
            len(self.fee_by_currency_id) == 1 and self.tx_fee >= 0,
            "Tx fee must be non-negative.",
        )
        enforce(self.nb_agents > 1, "Must have at least two agents.")
        enforce(self.nb_goods > 1, "Must have at least two goods.")
        enforce(
            len(self.agent_addresses) == self.nb_agents,
            "There must be one address for each agent.",
        )
        enforce(
            len(set(self.agent_names)) == self.nb_agents,
            "Agents' names must be unique.",
        )
        enforce(
            len(self.good_ids) == self.nb_goods, "There must be one id for each good."
        )
        enforce(
            len(set(self.good_names)) == self.nb_goods, "Goods' names must be unique."
        )


class Game(Model):
    """This class deals with the game."""

    def __init__(self, **kwargs: Any):
        """Instantiate the game class."""
        self._expected_controller_addr = kwargs.pop(
            "expected_controller_addr", None
        )  # type: Optional[str]

        self._search_query = kwargs.pop("search_query", DEFAULT_SEARCH_QUERY)
        if "search_value" not in self._search_query:  # pragma: nocover
            raise ValueError("search_value not found in search_query")
        self._expected_version_id = self._search_query["search_value"]
        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = Location(
            latitude=location["latitude"], longitude=location["longitude"]
        )
        self._radius = kwargs.pop("search_radius", DEFAULT_SEARCH_RADIUS)

        ledger_id = kwargs.pop("ledger_id", None)
        self._is_using_contract = kwargs.pop("is_using_contract", False)  # type: bool
        super().__init__(**kwargs)
        self._phase = Phase.PRE_GAME
        self._conf = None  # type: Optional[Configuration]
        self._contract_address = None  # type: Optional[str]
        self._tac_dialogue = None  # type: Optional[TacDialogue]
        self._state_update_dialogue = None  # type: Optional[StateUpdateDialogue]
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_using_contract(self) -> bool:
        """Returns the is_using_contract."""
        return self._is_using_contract

    @property
    def expected_version_id(self) -> str:
        """Get the expected version id of the TAC."""
        return self._expected_version_id

    @property
    def phase(self) -> Phase:
        """Get the game phase."""
        return self._phase

    @property
    def contract_address(self) -> str:
        """Get the contract address."""
        if self._contract_address is None:
            raise AEAEnforceError("Contract address not set!")
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address."""
        enforce(self._contract_address is None, "Contract address already set!")
        self._contract_address = contract_address

    @property
    def tac_dialogue(self) -> TacDialogue:
        """Retrieve the tac dialogue."""
        if self._tac_dialogue is None:
            raise AEAEnforceError("TacDialogue not set!")
        return self._tac_dialogue

    @tac_dialogue.setter
    def tac_dialogue(self, tac_dialogue: TacDialogue) -> None:
        """Set the tac dialogue."""
        enforce(self._tac_dialogue is None, "TacDialogue already set!")
        self._tac_dialogue = tac_dialogue

    @property
    def state_update_dialogue(self) -> StateUpdateDialogue:
        """Retrieve the state_update dialogue."""
        if self._state_update_dialogue is None:
            raise AEAEnforceError("StateUpdateDialogue not set!")
        return self._state_update_dialogue

    @state_update_dialogue.setter
    def state_update_dialogue(self, state_update_dialogue: StateUpdateDialogue) -> None:
        """Set the state_update dialogue."""
        enforce(self._state_update_dialogue is None, "StateUpdateDialogue already set!")
        self._state_update_dialogue = state_update_dialogue

    @property
    def expected_controller_addr(self) -> Address:
        """Get the expected controller address."""
        if self._expected_controller_addr is None:
            raise AEAEnforceError("Expected controller address not assigned!")
        return self._expected_controller_addr

    @property
    def conf(self) -> Configuration:
        """Get the game configuration."""
        if self._conf is None:
            raise AEAEnforceError("Game configuration not assigned!")
        return self._conf

    def init(self, tac_message: TacMessage, controller_addr: Address) -> None:
        """
        Populate data structures with the game data.

        :param tac_message: the tac message with the game instance data
        :param controller_addr: the address of the controller
        """
        enforce(
            tac_message.performative == TacMessage.Performative.GAME_DATA,
            "Wrong TacMessage for initialization of TAC game.",
        )
        enforce(
            controller_addr == self.expected_controller_addr,
            "TacMessage from unexpected controller.",
        )
        enforce(
            tac_message.version_id == self.expected_version_id,
            f"TacMessage for unexpected game, expected={self.expected_version_id}, found={tac_message.version_id}",
        )
        self._conf = Configuration(
            tac_message.version_id,
            tac_message.fee_by_currency_id,
            tac_message.agent_addr_to_name,
            tac_message.good_id_to_name,
            controller_addr,
        )

    def update_expected_controller_addr(self, controller_addr: Address) -> None:
        """
        Overwrite the expected controller address.

        :param controller_addr: the address of the controller
        """
        self.context.logger.warning(
            "TAKE CARE! Circumventing controller identity check! For added security provide the expected controller key as an argument to the Game instance and check against it."
        )
        self._expected_controller_addr = controller_addr

    def update_game_phase(self, phase: Phase) -> None:
        """
        Update the game phase.

        :param phase: the game phase
        """
        self._phase = phase

    def get_game_query(self) -> Query:
        """
        Get the query for the TAC game.

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

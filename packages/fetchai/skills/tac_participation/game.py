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
from typing import Dict, List, Optional

from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.mail.base import Address
from aea.skills.base import Model

from packages.fetchai.protocols.tac.message import TacMessage

DEFAULT_LEDGER_ID = "ethereum"


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
        tx_fee: int,
        agent_addr_to_name: Dict[Address, str],
        good_id_to_name: Dict[str, str],
        controller_addr: Address,
    ):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param tx_fee: the fee for a transaction.
        :param agent_addr_to_name: a dictionary mapping agent addresses to agent names (as strings).
        :param good_id_to_name: a dictionary mapping good ids to good names (as strings).
        :param controller_addr: the address of the controller
        """
        self._version_id = version_id
        self._nb_agents = len(agent_addr_to_name)
        self._nb_goods = len(good_id_to_name)
        self._tx_fee = tx_fee
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
        return self._tx_fee

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
    def agent_names(self):
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

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert self.version_id is not None, "A version id must be set."
        assert self.tx_fee >= 0, "Tx fee must be non-negative."
        assert self.nb_agents > 1, "Must have at least two agents."
        assert self.nb_goods > 1, "Must have at least two goods."
        assert (
            len(self.agent_addresses) == self.nb_agents
        ), "There must be one address for each agent."
        assert (
            len(set(self.agent_names)) == self.nb_agents
        ), "Agents' names must be unique."
        assert (
            len(self.good_ids) == self.nb_goods
        ), "There must be one id for each good."
        assert (
            len(set(self.good_names)) == self.nb_goods
        ), "Goods' names must be unique."


class Game(Model):
    """This class deals with the game."""

    def __init__(self, **kwargs):
        """Instantiate the game class."""
        self._expected_version_id = kwargs.pop("expected_version_id", "")  # type: str
        self._expected_controller_addr = kwargs.pop(
            "expected_controller_addr", None
        )  # type: Optional[str]
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._is_using_contract = kwargs.pop("is_using_contract", False)  # type: bool
        super().__init__(**kwargs)
        self._phase = Phase.PRE_GAME
        self._conf = None  # type: Optional[Configuration]
        self._contract_address = None  # type: Optional[str]

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
        assert self._contract_address is not None, "Contract address not set!"
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address."""
        assert self._contract_address is None, "Contract address already set!"
        self._contract_address = contract_address

    @property
    def expected_controller_addr(self) -> Address:
        """Get the expected controller pbk."""
        assert (
            self._expected_controller_addr is not None
        ), "Expected controller address not assigned!"
        return self._expected_controller_addr

    @property
    def conf(self) -> Configuration:
        """Get the game configuration."""
        assert self._conf is not None, "Game configuration not assigned!"
        return self._conf

    def init(self, tac_message: TacMessage, controller_addr: Address) -> None:
        """
        Populate data structures with the game data.

        :param tac_message: the tac message with the game instance data
        :param controller_addr: the address of the controller

        :return: None
        """
        assert (
            tac_message.performative == TacMessage.Performative.GAME_DATA
        ), "Wrong TacMessage for initialization of TAC game."
        assert (
            controller_addr == self.expected_controller_addr
        ), "TacMessage from unexpected controller."
        assert (
            tac_message.version_id == self.expected_version_id
        ), "TacMessage for unexpected game."
        self._conf = Configuration(
            tac_message.version_id,
            tac_message.tx_fee,
            tac_message.agent_addr_to_name,
            tac_message.good_id_to_name,
            controller_addr,
        )

    def update_expected_controller_addr(self, controller_addr: Address):
        """
        Overwrite the expected controller pbk.

        :param controller_addr: the address of the controller

        :return: None
        """
        self.context.logger.warning(
            "[{}]: TAKE CARE! Circumventing controller identity check! For added security provide the expected controller key as an argument to the Game instance and check against it.".format(
                self.context.agent_name
            )
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
        query = Query(
            [Constraint("version", ConstraintType("==", self.expected_version_id))]
        )
        return query

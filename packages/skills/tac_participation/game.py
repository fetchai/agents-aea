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
import logging
from typing import Dict, List, Optional, cast, TYPE_CHECKING

from aea.protocols.oef.models import Query, Constraint, ConstraintType
from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
else:
    from tac_protocol.message import TACMessage

Address = str

logger = logging.getLogger("aea.tac_participation_skill")


class Phase(Enum):
    """This class defines the phases of the game."""

    PRE_GAME = 'pre_game'
    GAME_REGISTRATION = 'game_registration'
    GAME_SETUP = 'game_setup'
    GAME = 'game'
    POST_GAME = 'post_game'


class GameConfiguration:
    """Class containing the game configuration of a TAC instance."""

    def __init__(self,
                 version_id: str,
                 nb_agents: int,
                 nb_goods: int,
                 tx_fee: int,
                 agent_pbk_to_name: Dict[Address, str],
                 good_pbk_to_name: Dict[Address, str],
                 controller_pbk: Address):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param nb_agents: the number of agents.
        :param nb_goods: the number of goods.
        :param tx_fee: the fee for a transaction.
        :param agent_pbk_to_name: a dictionary mapping agent public keys to agent names (as strings).
        :param good_pbk_to_name: a dictionary mapping good public keys to good names (as strings).
        :param controller_pbk: the public key of the controller
        """
        self._version_id = version_id
        self._nb_agents = nb_agents
        self._nb_goods = nb_goods
        self._tx_fee = tx_fee
        self._agent_pbk_to_name = agent_pbk_to_name
        self._good_pbk_to_name = good_pbk_to_name
        self._controller_pbk = controller_pbk

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
    def agent_pbk_to_name(self) -> Dict[Address, str]:
        """Map agent public keys to names."""
        return self._agent_pbk_to_name

    @property
    def good_pbk_to_name(self) -> Dict[Address, str]:
        """Map good public keys to names."""
        return self._good_pbk_to_name

    @property
    def agent_pbks(self) -> List[Address]:
        """List of agent public keys."""
        return list(self._agent_pbk_to_name.keys())

    @property
    def agent_names(self):
        """List of agent names."""
        return list(self._agent_pbk_to_name.values())

    @property
    def good_pbks(self) -> List[Address]:
        """List of good public keys."""
        return list(self._good_pbk_to_name.keys())

    @property
    def good_names(self) -> List[str]:
        """List of good names."""
        return list(self._good_pbk_to_name.values())

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
        assert len(self.agent_pbks) == self.nb_agents, "There must be one public key for each agent."
        assert len(set(self.agent_names)) == self.nb_agents, "Agents' names must be unique."
        assert len(self.good_pbks) == self.nb_goods, "There must be one public key for each good."
        assert len(set(self.good_names)) == self.nb_goods, "Goods' names must be unique."


class Game(SharedClass):
    """This class deals with the game."""

    def __init__(self, **kwargs):
        """Instantiate the game class."""
        self._expected_version_id = kwargs.pop('expected_version_id', '')  # type: str
        self._expected_controller_pbk = kwargs.pop('expected_controller_pbk', None)  # type: Optional[str]
        super().__init__(**kwargs)
        self._phase = Phase.PRE_GAME
        self._game_configuration = None  # type: Optional[GameConfiguration]

    @property
    def expected_version_id(self) -> str:
        """Get the expected version id of the TAC."""
        return self._expected_version_id

    @property
    def phase(self) -> Phase:
        """Get the game phase."""
        return self._phase

    @property
    def expected_controller_pbk(self) -> Address:
        """Get the expected controller pbk."""
        assert self._expected_controller_pbk is not None, "Expected controller public key not assigned!"
        return self._expected_controller_pbk

    @property
    def game_configuration(self) -> GameConfiguration:
        """Get the game configuration."""
        assert self._game_configuration is not None, "Game configuration not assigned!"
        return self._game_configuration

    def init(self, tac_message: TACMessage, controller_pbk: Address) -> None:
        """
        Populate data structures with the game data.

        :param tac_message: the tac message with the game instance data
        :param controller_pbk: the public key of the controller

        :return: None
        """
        assert tac_message.get("type") == TACMessage.Type.GAME_DATA, "Wrong TACMessage for initialization of TAC game."
        assert controller_pbk == self.expected_controller_pbk, "TACMessage from unexpected controller."
        assert tac_message.get("version_id") == self.expected_version_id, "TACMessage for unexpected game."
        self._game_configuration = GameConfiguration(cast(str, tac_message.get("version_id")),
                                                     cast(int, tac_message.get("nb_agents")),
                                                     cast(int, tac_message.get("nb_goods")),
                                                     cast(int, tac_message.get("tx_fee")),
                                                     cast(Dict[str, str], tac_message.get("agent_pbk_to_name")),
                                                     cast(Dict[str, str], tac_message.get("good_pbk_to_name")),
                                                     controller_pbk)

    def update_expected_controller_pbk(self, controller_pbk: Address):
        """
        Overwrite the expected controller pbk.

        :param controller_pbk: the public key of the controller

        :return: None
        """
        logger.warning("TAKE CARE! Circumventing controller identity check! For added security provide the expected controller key as an argument to the Game instance and check against it.")
        self._expected_controller_pbk = controller_pbk

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
        query = Query([Constraint("version", ConstraintType("==", self.expected_version_id))])
        return query

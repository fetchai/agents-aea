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

"""This package contains a scaffold of a handler."""

from typing import Optional

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.skills.base import Handler


class MyScaffoldHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = ''  # type: Optional[ProtocolId]

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def expected_version_id(self) -> str:
        """Get the expected version id of the TAC."""
        return self._expected_version_id

    @property
    def game_phase(self) -> GamePhase:
        """Get the game phase."""
        return self._game_phase

    @property
    def game_configuration(self) -> GameConfiguration:
        """Get the game configuration."""
        assert self._game_configuration is not None, "Game configuration not assigned!"
        return self._game_configuration

    def init(self, game_data: GameData, agent_pbk: Address) -> None:
        """
        Populate data structures with the game data.

        :param game_data: the game instance data
        :param agent_pbk: the public key of the agent

        :return: None
        """
        # TODO: extend TAC messages to include reference to version id; then replace below with assert
        game_data.version_id = self.expected_version_id
        self._game_configuration = GameConfiguration(game_data.version_id, game_data.nb_agents, game_data.nb_goods, game_data.tx_fee,
                                                     game_data.agent_pbk_to_name, game_data.good_pbk_to_name)
        self._initial_agent_state = AgentState(game_data.money, game_data.endowment, game_data.utility_params)
        self._agent_state = AgentState(game_data.money, game_data.endowment, game_data.utility_params)
        if self.strategy.is_world_modeling:
            opponent_pbks = self.game_configuration.agent_pbks
            opponent_pbks.remove(agent_pbk)
            self._world_state = WorldState(opponent_pbks, self.game_configuration.good_pbks, self.initial_agent_state)

    def on_state_update(self, message: TACMessage, agent_pbk: Address) -> None:
        """
        Update the game instance with a State Update from the controller.

        :param state_update: the state update
        :param agent_pbk: the public key of the agent

        :return: None
        """
        self.init(message.get("initial_state"), agent_pbk)
        self._game_phase = GamePhase.GAME
        for tx in message.get("transactions"):
            self.agent_state.update(tx, message.get("initial_state").get("tx_fee"))

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

game.controller_pbk

game._game_phase

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


        # game_data = GameData(sender,
        #                      tac_message.get("money"),
        #                      tac_message.get("endowment"),
        #                      tac_message.get("utility_params"),
        #                      tac_message.get("nb_agents"),
        #                      tac_message.get("nb_goods"),
        #                      tac_message.get("tx_fee"),
        #                      tac_message.get("agent_pbk_to_name"),
        #                      tac_message.get("good_pbk_to_name"),
        #                      tac_message.get("version_id"))
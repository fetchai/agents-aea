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

"""This package contains a the behaviours."""

import logging
from typing import cast, TYPE_CHECKING

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.model import Description, DataModel, Attribute
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.skills.base import Behaviour

if TYPE_CHECKING:
    from packages.skills.tac_control.game import Game, GamePhase
else:
    from tac_control_skill.game import Game, GamePhase

CONTROLLER_DATAMODEL = DataModel("tac", [
    Attribute("version", str, True, "Version number of the TAC Controller Agent."),
])

logger = logging.getLogger("aea.tac_control_skill")


class TACBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        game = cast(Game, self.context.game)
        if game.game_phase == GamePhase.PRE_GAME:
            self._register_tac()
        elif game.game_phase == GamePhase.PRE_SETUP and game.time_to_start:
            self._start_tac()
        elif 
        elif game.game_phase == GamePhase.POST_GAME

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass

    def _register_tac(self) -> None:
        """
        Register on the OEF as a TAC controller agent.

        :return: None.
        """
        desc = Description({"version": self.tac_version_id}, data_model=CONTROLLER_DATAMODEL)
        logger.debug("[{}]: Registering with {} data model".format(self.context.agent_name, desc.data_model.name))
        msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=1, service_description=desc, service_id="")
        msg_bytes = OEFSerializer().encode(msg)
        self.mailbox.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto.public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

    def _start_tac(self):
        """Create a game and send the game configuration to every registered agent."""
        game = cast(Game, self.context.game)
        game.create()
        logger.debug("[{}]: Started competition:\n{}".format(self.context.agent_name, game.get_holdings_summary()))
        logger.debug("[{}]: Computed equilibrium:\n{}".format(self.context.agent_name, game.get_equilibrium_summary()))
        for public_key in game.configuration.agent_pbks:
            agent_state = game.get_agent_state_from_agent_pbk(public_key)
            game_data_response = GameData(
                public_key,
                agent_state.balance,
                agent_state.current_holdings,
                agent_state.utility_params,
                self.current_game.configuration.nb_agents,
                self.current_game.configuration.nb_goods,
                self.current_game.configuration.tx_fee,
                self.current_game.configuration.agent_pbk_to_name,
                self.current_game.configuration.good_pbk_to_name,
                self.current_game.configuration.version_id
            )
            msg = TACMessage(tac_type=TACMessage.Type.GAME_DATA,
                             money=agent_state.balance,
                             endowment=agent_state.current_holdings,
                             utility_params=agent_state.utility_params,
                             nb_agents=game.configuration.nb_agents,
                             nb_goods=game.configuration.nb_goods,
                             tx_fee=game.configuration.tx_fee,
                             agent_pbk_to_name=game.configuration.agent_pbk_to_name,
                             good_pbk_to_name=game.configuration.good_pbk_to_name,
                             version_id=game.configuration.version_id
                             )
            logger.debug("[{}]: sending game data to '{}': {}"
                         .format(self.context.agent_name, public_key, str(msg)))
            self.mailbox.outbox.put_message(to=public_key, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=TACSerializer().encode(msg))

    def _cancel_tac(self):
        """Notify agents that the TAC is cancelled."""
        game = cast(Game, self.context.game)
        logger.debug("[{}]: Notifying agents that TAC is cancelled.".format(self.context.agent_name))
        for agent_pbk in game.registered_agents:
            tac_msg = TACMessage(tac_type=TACMessage.Type.CANCELLED)
            self.mailbox.outbox.put_message(to=agent_pbk, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=TACSerializer().encode(tac_msg))

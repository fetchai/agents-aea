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

import datetime
import logging
from typing import cast, TYPE_CHECKING

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description, DataModel, Attribute
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.skills.base import Behaviour

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
    from packages.protocols.tac.serialization import TACSerializer
    from packages.skills.tac_control.game import Game, Phase
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_protocol.serialization import TACSerializer
    from tac_control_skill.game import Game, Phase
    from tac_control_skill.parameters import Parameters

CONTROLLER_DATAMODEL = DataModel("tac", [
    Attribute("version", str, True, "Version number of the TAC Controller Agent."),
])

logger = logging.getLogger("aea.tac_control_skill")


class TACBehaviour(Behaviour):
    """This class implements the TAC control behaviour."""

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
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        if game.phase == Phase.PRE_GAME and parameters.registration_start_time > now:
            game.phase = Phase.GAME_REGISTRATION
            self._register_tac()
        elif game.phase == Phase.GAME_REGISTRATION and parameters.start_time > now:
            if game.registration.nb_agents < parameters.min_nb_agents:
                game.phase = Phase.POST_GAME
                self._cancel_tac()
            else:
                game.phase = Phase.GAME_SETUP
                self._start_tac()
        elif game.phase == Phase.GAME and parameters.end_time > now:
            game.phase = Phase.POST_GAME
            self._cancel_tac()

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
        desc = Description({"version": self.context.parameters.version_id}, data_model=CONTROLLER_DATAMODEL)
        logger.debug("[{}]: Registering with data model".format(self.context.agent_name))
        msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=1, service_description=desc, service_id="")
        self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=OEFSerializer().encode(msg))

    def _start_tac(self):
        """Create a game and send the game configuration to every registered agent."""
        game = cast(Game, self.context.game)
        game.create()
        logger.debug("[{}]: Started competition:\n{}".format(self.context.agent_name, game.get_holdings_summary()))
        logger.debug("[{}]: Computed equilibrium:\n{}".format(self.context.agent_name, game.get_equilibrium_summary()))
        for agent_public_key in game.configuration.agent_pbks:
            agent_state = game.current_agent_states[agent_public_key]
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
                         .format(self.context.agent_name, agent_public_key, str(msg)))
            self.mailbox.outbox.put_message(to=agent_public_key, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=TACSerializer().encode(msg))

    def _cancel_tac(self):
        """Notify agents that the TAC is cancelled."""
        game = cast(Game, self.context.game)
        logger.debug("[{}]: Notifying agents that TAC is cancelled.".format(self.context.agent_name))
        for agent_pbk in game.registration.agent_pbk_to_name.keys():
            tac_msg = TACMessage(tac_type=TACMessage.Type.CANCELLED)
            self.mailbox.outbox.put_message(to=agent_pbk, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=TACSerializer().encode(tac_msg))

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

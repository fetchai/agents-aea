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

"""This package contains a scaffold of a behaviour."""

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.skills.base import Behaviour

from tac_skill.game import GamePhase


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
        if self.context.game.game_phase == GamePhase.PRE_GAME:
            self._search_for_tac()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass

    def _search_for_tac(self) -> None:
        """
        Search for active TAC Controller.

        We assume that the controller is registered as a service with the 'tac' data model
        and with an attribute version = expected_version_id.

        :return: None
        """
        query = self.context.game.get_game_query()
        search_id = self.context.search.get_next_id()
        self.context.search.ids_for_tac.add(search_id)
        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query)
        msg_bytes = OEFSerializer().encode(msg)
        self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

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

from aea.protocols.oef.message import OEFMessage, DEFAULT_OEF
from aea.protocols.oef.serialization import OEFSerializer
from aea.protocols.oef.models import Query, Constraint, GtEq
from aea.protocols.tac.message import TACMessage
from aea.protocols.tac.serialization import TACSerializer
from aea.skills.base import Behaviour


class TACBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

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
        raise NotImplementedError  # pragma: no cover

    def _search_for_tac(self) -> None:
        """
        Search for active TAC Controller.

        We assume that the controller is registered as a service with the 'tac' data model
        and with an attribute version = expected_version_id.

        :return: None
        """
        query = Query([Constraint("version", GtEq(self.game_instance.expected_version_id))])
        search_id = self.game_instance.search.get_next_id()
        self.game_instance.search.ids_for_tac.add(search_id)

        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query)
        msg_bytes = OEFSerializer().encode(msg)
        self.mailbox.outbox.put_message(to=DEFAULT_OEF, sender=self.crypto.public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)


    # def request_state_update(self) -> None:
    #     """
    #     Request current agent state from TAC Controller.

    #     :return: None
    #     """
    #     tac_msg = TACMessage(tac_type=TACMessage.Type.GET_STATE_UPDATE)
    #     tac_bytes = TACSerializer().encode(tac_msg)
    #     self.mailbox.outbox.put_message(to=self.game_instance.controller_pbk, sender=self.crypto.public_key,
    #                                     protocol_id=TACMessage.protocol_id, message=tac_bytes)



    #     self._expected_version_id = expected_version_id

    #     self._game_configuration = None  # type: Optional[GameConfiguration]
    #     self._initial_agent_state = None  # type: Optional[AgentState]
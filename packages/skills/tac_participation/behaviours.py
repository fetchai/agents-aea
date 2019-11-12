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

"""This package contains a tac participation behaviour."""

import logging
from typing import cast, TYPE_CHECKING

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF
from aea.skills.base import Behaviour

if TYPE_CHECKING:
    from packages.skills.tac_participation.game import Game, Phase
    from packages.skills.tac_participation.search import Search
else:
    from tac_participation_skill.game import Game, Phase
    from tac_participation_skill.search import Search

logger = logging.getLogger("aea.tac_participation_skill")


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
        search = cast(Search, self.context.search)
        if game.phase.value == Phase.PRE_GAME.value and search.is_time_to_search():
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
        game = cast(Game, self.context.game)
        search = cast(Search, self.context.search)
        query = game.get_game_query()
        search_id = search.get_next_id()
        search.ids_for_tac.add(search_id)
        logger.debug("[{}]: Searching for TAC, search_id={}".format(self.context.agent_name, search_id))
        msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query)
        msg_bytes = OEFSerializer().encode(msg)
        self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

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

import logging
import time

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Query, Constraint, ConstraintType
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from aea.skills.base import Behaviour

logger = logging.getLogger("aea.my_search_skill")


class MySearchBehaviour(Behaviour):
    """This class provides a simple search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        super().__init__(**kwargs)
        self.sent_search_count = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        logger.info("[{}]: setting up MySearchBehaviour".format(self.context.agent_name))

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        time.sleep(1)  # to slow down the agent
        self.sent_search_count += 1

        self.sent_search_count += 1
        search_constraints = [Constraint("country", ConstraintType("==", "UK"))]

        search_query_w_empty_model = Query(search_constraints, model=None)

        search_request = OEFMessage(
            oef_type=OEFMessage.Type.SEARCH_SERVICES,
            id=self.sent_search_count,
            query=search_query_w_empty_model)

        logger.info("[{}]: sending search request to OEF, search_count={}".format(
            self.context.agent_name,
            self.sent_search_count))

        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(search_request))

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        logger.info("[{}]: tearing down MySearchBehaviour".format(self.context.agent_name))
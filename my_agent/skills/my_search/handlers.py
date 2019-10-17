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
import logging

from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer
from aea.skills.base import Handler

logger = logging.getLogger("aea.my_search_skill")


class MySearchHandler(Handler):
    """This class provides a simple search handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.received_search_count = 0

    def setup(self) -> None:
        """Set up the handler."""
        logger.info("[{}]: setting up MySearchHandler".format(self.context.agent_name))

    def handle(self, message: OEFMessage, sender: str) -> None:
        """
        Handle the message.

        :param message: the message.
        :param sender: the sender.
        :return: None
        """
        return
        msg_type = OEFMessage.Type(message.get("type"))

        if msg_type is OEFMessage.Type.SEARCH_RESULT:
            self.received_search_count += 1
            nb_agents_found = len(message.get("agents"))
            logger.info("[{}]: found number of agents={}, received search count={}".format(self.context.agent_name, nb_agents_found, self.received_search_count))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        logger.info("[{}]: tearing down MySearchHandler".format(self.context.agent_name))

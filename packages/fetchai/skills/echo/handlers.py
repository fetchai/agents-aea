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

"""This module contains the handler for the 'echo' skill."""

from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler


class EchoHandler(Handler):
    """Echo handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("Echo Handler: setup method called.")

    def handle(self, message: Message) -> None:
        """
        Handle the message.

        :param message: the message.
        :return: None
        """
        self.context.logger.info(
            "Echo Handler: message={}, sender={}".format(message, message.counterparty)
        )
        self.context.outbox.put_message(sender=self.context.agent_name, message=message)

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        self.context.logger.info("Echo Handler: teardown method called.")

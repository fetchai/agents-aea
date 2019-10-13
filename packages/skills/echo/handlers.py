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
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler


class EchoHandler(Handler):
    """Echo handler."""

    SUPPORTED_PROTOCOL = "default"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        print("EchoHandler.__init__: arguments: {}".format(kwargs))

    def setup(self) -> None:
        """Set up the handler."""
        print("Echo Handler: setup method called.")

    def handle(self, message: Message, sender: str) -> None:
        """
        Handle the message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        print("Echo Handler: received message: {}, sender={}".format(message, sender))
        self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id="default",
                                        message=DefaultSerializer().encode(message))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        print("Echo Handler: teardown method called.")

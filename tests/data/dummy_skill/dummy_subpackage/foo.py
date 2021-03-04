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

"""This module is in a skill sub-package (for testing purposes)."""
from aea.protocols.base import Message
from aea.skills.base import Behaviour, Handler

from packages.fetchai.protocols.state_update import StateUpdateMessage


def bar():
    """A bar function."""
    return 42


class DummyBehaviour(Behaviour):
    """Dummy behaviour."""

    def __init__(self, **kwargs):
        """Initialize the dummy behaviour."""
        super().__init__(**kwargs)
        self.kwargs = kwargs

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """Act according to the behaviour."""

    def teardown(self) -> None:
        """Teardown the behaviour."""


class DummyStateUpdateHandler(Handler):
    """Dummy handler."""

    SUPPORTED_PROTOCOL = StateUpdateMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Handle message.

        :param message: the message
        :return: None
        """

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """

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
"""Fake connection to generate test messages."""
from typing import Optional

from aea.connections.base import Connection
from aea.mail.base import Envelope


class FakeConnection(Connection):
    """Simple fake connection to populate inbox."""

    def __init__(self, envelope: Envelope, num: int, *args, **kwargs):
        """
        Set fake connection with num of envelops to be generated.

        :param envelope: any envelope
        :param num: amount of envelopes to generate
        """
        Connection.__init__(self, *args, **kwargs)
        self.num = num
        self.envelope = envelope
        self.connection_status.is_connected = True

    async def connect(self) -> None:
        """
        Do nothing. always connected.

        :return: None
        """

    async def disconnect(self) -> None:
        """
        Disconnect. just set a flag.

        :return: None
        """
        self.connection_status.is_connected = False

    async def send(self, envelope: Envelope) -> None:
        """
        Do not send custom envelops. Only generates.

        :param envelope: envelope to send.
        :return: None
        """
        return None

    async def receive(self, *args, **kwargs) -> Optional[Envelope]:
        """
        Return envelope set `num` times.

        :return: incoming envelope
        """
        if self.num > 0:
            self.num -= 1

        return self.envelope

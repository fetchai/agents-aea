# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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
import asyncio
from typing import Any, Optional

from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope


class FakeConnection(Connection):
    """Simple fake connection to populate inbox."""

    def __init__(self, envelope: Envelope, num: int, *args: Any, **kwargs: Any):
        """
        Set fake connection with number of envelops to be generated.

        :param envelope: any envelope
        :param num: amount of envelopes to generate
        :param args: positional arguments
        :param kwargs: keyword arguments
        """
        Connection.__init__(self, *args, **kwargs)
        self.num = num
        self.envelope = envelope
        self.state = ConnectionStates.connected

    async def connect(self) -> None:
        """Do nothing. always connected."""

    async def disconnect(self) -> None:
        """Disconnect. just set a flag."""
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """
        Do not send custom envelops. Only generates.

        :param envelope: envelope to send.
        :return: None
        """
        return None

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """
        Return envelope set `num` times.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: incoming envelope
        """
        if self.num <= 0:
            await asyncio.sleep(0.1)  # sleep to avoid multiplexer loop without idle.
            return None

        self.num -= 1
        return self.envelope

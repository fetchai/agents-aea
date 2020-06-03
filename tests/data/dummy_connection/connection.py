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

"""This module contains the implementation of a 'dummy' connection useful for testing."""

import asyncio
from concurrent.futures._base import CancelledError
from typing import Optional

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope


class DummyConnection(Connection):
    """A dummy connection that just stores the messages."""

    connection_id = PublicId("fetchai", "dummy", "0.1.0")

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.connection_status.is_connected = False
        self._queue = None

    async def connect(self, *args, **kwargs):
        """Connect."""
        self._queue = asyncio.Queue(loop=self.loop)
        self.connection_status.is_connected = True

    async def disconnect(self, *args, **kwargs):
        """Disconnect."""
        await self._queue.put(None)
        self.connection_status.is_connected = False

    async def send(self, envelope: "Envelope"):
        """Send an envelope."""
        assert self._queue is not None
        self._queue.put_nowait(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """Receive an envelope."""
        try:
            assert self._queue is not None
            envelope = await self._queue.get()
            if envelope is None:
                return None
            return envelope
        except CancelledError:
            return None
        except Exception as e:
            print(str(e))
            return None

    def put(self, envelope: Envelope):
        """Put an envelope in the queue."""
        assert self._queue is not None
        self._queue.put_nowait(envelope)

    @classmethod
    def from_config(
        cls, configuration: ConnectionConfig, identity: Identity, cryptos: CryptoStore
    ) -> "Connection":
        """
        Get the dummy connection from the connection configuration.

        :param configuration: the connection configuration.
        :param identity: the identity object.
        :param cryptos: object to access the connection crypto objects.
        :return: the connection object
        """
        return DummyConnection(
            configuration=configuration, identity=identity, cryptos=cryptos
        )

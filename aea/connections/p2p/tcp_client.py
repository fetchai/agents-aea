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

"""Implementation of the TCP server."""
import asyncio
import logging
from asyncio import AbstractEventLoop, Task, StreamWriter, StreamReader
from threading import Thread
from typing import Optional, cast

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.connections.p2p.base import TCPChannel, TCPConnection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPClientChannel(TCPChannel):
    """Channel implementation for the local node."""

    def __init__(self, public_key: str, address: str, unix: bool = True, loop: Optional[AbstractEventLoop] = None):
        """
        Initialize a TCP channel.

        :param public_key: the public key.
        :param address: the socket bind address.
        :param unix: whether it's a unix server or a networked.
        :param loop: the asyncio loop.
        """
        super().__init__(public_key)
        self.address = address
        self.unix = unix
        self._loop = asyncio.new_event_loop() if loop is None else loop
        self._thread = None  # type: Optional[Thread]

        self._reader, self._writer = (None, None)  # type: Optional[StreamReader], Optional[StreamWriter]
        self._read_task = None  # type: Optional[Task]

    def connect(self):
        """
        Set up the connection.

        :return: A queue or None.
        """
        self._thread = Thread(target=self._loop.run_forever)
        self._thread.start()

        if self.unix:
            coro = asyncio.open_unix_connection(path=self.address, loop=self._loop)
        else:
            ip, port = self.address.split(":")
            port = int(port)
            coro = asyncio.open_connection(ip, port, loop=self._loop, start_serving=False)

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        self._reader, self._writer = future.result()

        public_key_bytes = self.public_key.encode("utf-8")
        future = asyncio.run_coroutine_threadsafe(self._send(self._writer, public_key_bytes), loop=self._loop)
        future.result()

        asyncio.run_coroutine_threadsafe(self._recv_loop(self._reader), self._loop)

    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """
        if self._stopped:
            return

        self._stopped = True
        self._writer = cast(StreamWriter, self._writer)
        self._thread = cast(Thread, self._thread)

        self._writer.close()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        self._writer = cast(StreamWriter, self._writer)
        asyncio.run_coroutine_threadsafe(self._send(self._writer, envelope.encode()), loop=self._loop)


class TCPClientConnection(TCPConnection):
    """Implementation of a TCP server connection."""

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the Local OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        address = cast(str, connection_configuration.config.get("address"))
        channel = TCPClientChannel(public_key, address, unix=True)
        return TCPClientConnection(public_key, channel)

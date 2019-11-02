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
from asyncio import AbstractEventLoop, StreamReader, StreamWriter, Task, AbstractServer
from typing import Dict, Optional, Tuple, cast

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.connections.tcp.base import TCPConnection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPServerConnection(TCPConnection):
    """Abstract TCP channel."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int,
                 loop: Optional[AbstractEventLoop] = None):
        """
        Initialize a TCP channel.

        :param public_key: public key.
        :param host: the socket bind address.
         :param loop: the asyncio loop.
        """
        super().__init__(public_key, host, port, loop=loop)

        self._server = None  # type: Optional[AbstractServer]
        self._server_task = None  # type: Optional[Task]
        self.connections = {}  # type: Dict[str, Tuple[StreamReader, StreamWriter]]
        self._read_tasks = set()

    async def handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle new connections.

        :param reader: the stream reader.
        :param writer: the stream writer.
        :return: None
        """
        logger.debug("Waiting for client public key...")
        public_key_bytes = await self._recv(reader)
        if public_key_bytes:
            public_key_bytes = cast(bytes, public_key_bytes)
            public_key = public_key_bytes.decode("utf-8")
            logger.debug("Public key of the client: {}".format(public_key))
            self.connections[public_key] = (reader, writer)
            task = self._loop.create_task(self._recv_loop(reader))
            self._read_tasks.add(task)

    def setup(self):
        """Set the connection up."""
        future = self._run_task(asyncio.start_server(self.handle, host=self.host, port=self.port,
                                                     loop=self._loop, start_serving=False))
        self._server = future.result()
        self._server_task = self._run_task(self._server.serve_forever())
        self._fetch_task = self._run_task(self._send_loop())

    def teardown(self):
        """Tear the connection down."""
        for t in self._read_tasks:
            t.cancel()
        self._server.close()

    def select_writer_from_envelope(self, envelope: Envelope):
        """Select the destination, given the envelope."""
        to = envelope.to
        if to not in self.connections:
            return None
        _, writer = self.connections[to]
        return writer

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the TCP server connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        address = cast(str, connection_configuration.config.get("address"))
        port = cast(int, connection_configuration.config.get("port"))
        return TCPServerConnection(public_key, address, port)

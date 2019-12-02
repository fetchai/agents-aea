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
from asyncio import StreamReader, StreamWriter, AbstractServer, Future
from typing import Dict, Optional, Tuple, cast

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.connections.tcp.base import TCPConnection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPServerConnection(TCPConnection):
    """This class implements a TCP server."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int,
                 connection_id: str = "tcp_server",
                 **kwargs):
        """
        Initialize a TCP channel.

        :param public_key: public key.
        :param host: the socket bind address.
        """
        super().__init__(public_key, host, port, connection_id, **kwargs)

        self._server = None  # type: Optional[AbstractServer]
        self.connections = {}  # type: Dict[str, Tuple[StreamReader, StreamWriter]]

        self._read_tasks_to_public_key = dict()  # type: Dict[Future, str]

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
            read_task = asyncio.ensure_future(self._recv(reader), loop=self._loop)
            self._read_tasks_to_public_key[read_task] = public_key

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope.

        :return: the received envelope, or None if an error occurred.
        """
        if len(self._read_tasks_to_public_key) == 0:
            logger.warning("Tried to read from the TCP server. However, there is no open connection to read from.")
            return None

        try:
            logger.debug("Waiting for incoming messages...")
            done, pending = await asyncio.wait(self._read_tasks_to_public_key.keys(), return_when=asyncio.FIRST_COMPLETED)  # type: ignore

            # take the first
            task = next(iter(done))
            envelope_bytes = task.result()
            if envelope_bytes is None:  # pragma: no cover
                logger.debug("[{}]: No data received.")
                return None
            envelope = Envelope.decode(envelope_bytes)
            public_key = self._read_tasks_to_public_key.pop(task)
            reader = self.connections[public_key][0]
            new_task = asyncio.ensure_future(self._recv(reader), loop=self._loop)
            self._read_tasks_to_public_key[new_task] = public_key
            return envelope
        except asyncio.CancelledError:
            logger.debug("Receiving loop cancelled.")
            return None
        except Exception as e:
            logger.error("Error in the receiving loop: {}".format(str(e)))
            return None

    async def setup(self):
        """Set the connection up."""
        self._server = await asyncio.start_server(self.handle, host=self.host, port=self.port)
        logger.debug("Start listening on {}:{}".format(self.host, self.port))

    async def teardown(self):
        """Tear the connection down."""
        for pbk, (reader, _) in self.connections.items():
            reader.feed_eof()

        for t in self._read_tasks_to_public_key:
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
        return TCPServerConnection(public_key, address, port,
                                   connection_id=connection_configuration.name,
                                   restricted_to_protocols=set(connection_configuration.restricted_to_protocols))

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
from asyncio import AbstractServer, Future, StreamReader, StreamWriter
from typing import Any, Dict, Optional, Tuple, cast

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.mail.base import Envelope

from packages.fetchai.connections.tcp.base import TCPConnection


_default_logger = logging.getLogger("aea.packages.fetchai.connections.tcp.tcp_server")

STUB_DIALOGUE_ID = 0


class TCPServerConnection(TCPConnection):
    """This class implements a TCP server."""

    def __init__(self, configuration: ConnectionConfig, **kwargs: Any) -> None:
        """
        Initialize a TCP server connection.

        :param configuration: the configuration object.
        :param kwargs: keyword arguments.
        """
        address = cast(str, configuration.config.get("address"))
        port = cast(int, configuration.config.get("port"))
        if address is None or port is None:
            raise ValueError("address and port must be set!")  # pragma: nocover
        super().__init__(address, port, configuration=configuration, **kwargs)
        self._server = None  # type: Optional[AbstractServer]
        self.connections = {}  # type: Dict[str, Tuple[StreamReader, StreamWriter]]

        self._read_tasks_to_address = dict()  # type: Dict[Future, Address]

    async def handle(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle new connections.

        :param reader: the stream reader.
        :param writer: the stream writer.
        """
        self.logger.debug("Waiting for client address...")
        address_bytes = await self._recv(reader)
        if address_bytes is not None:
            address_bytes = cast(bytes, address_bytes)
            address = address_bytes.decode("utf-8")
            self.logger.debug("Public key of the client: {}".format(address))
            self.connections[address] = (reader, writer)
            read_task = asyncio.ensure_future(self._recv(reader), loop=self.loop)
            self._read_tasks_to_address[read_task] = address

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the received envelope, or None if an error occurred.
        """
        if len(self._read_tasks_to_address) == 0:
            self.logger.warning(
                "Tried to read from the TCP server. However, there is no open connection to read from."
            )
            return None

        try:
            self.logger.debug("Waiting for incoming messages...")
            done, _ = await asyncio.wait(self._read_tasks_to_address.keys(), return_when=asyncio.FIRST_COMPLETED)  # type: ignore

            # take the first
            task = next(iter(done))
            envelope_bytes = task.result()
            if envelope_bytes is None:  # pragma: no cover
                self.logger.debug("[{}]: No data received.")
                return None
            envelope = Envelope.decode(envelope_bytes)
            address = self._read_tasks_to_address.pop(task)
            reader = self.connections[address][0]
            new_task = asyncio.ensure_future(self._recv(reader), loop=self.loop)
            self._read_tasks_to_address[new_task] = address
            return envelope
        except asyncio.CancelledError:
            self.logger.debug("Receiving loop cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.error("Error in the receiving loop: {}".format(str(e)))
            return None

    async def setup(self) -> None:
        """Set the connection up."""
        self._server = await asyncio.start_server(
            self.handle, host=self.host, port=self.port
        )
        self.logger.debug("Start listening on {}:{}".format(self.host, self.port))

    async def teardown(self) -> None:
        """Tear the connection down."""
        for (reader, _) in self.connections.values():
            reader.feed_eof()

        for t in self._read_tasks_to_address:
            t.cancel()

        if self._server is None:  # pragma: nocover
            raise ValueError("Server not set!")

        self._server.close()
        await self._server.wait_closed()

    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """Select the destination, given the envelope."""
        to = envelope.to
        if to not in self.connections:
            return None
        _, writer = self.connections[to]
        return writer

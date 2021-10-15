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

"""Base classes for TCP communication."""
import logging
import struct
from abc import ABC, abstractmethod
from asyncio import CancelledError, StreamReader, StreamWriter
from typing import Any, Optional

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope


_default_logger = logging.getLogger("aea.packages.fetchai.connections.tcp")

PUBLIC_ID = PublicId.from_str("fetchai/tcp:0.17.0")


class TCPConnection(Connection, ABC):
    """Abstract TCP connection."""

    connection_id = PUBLIC_ID

    def __init__(self, host: str, port: int, **kwargs: Any) -> None:
        """
        Initialize a TCP connection.

        :param host: the socket bind address.
        :param port: the socket bind port.
        :param kwargs: keyword arguments.
        """
        super().__init__(**kwargs)
        # for the server, the listening address/port
        # for the client, the server address/port
        self.host = host
        self.port = port

    @abstractmethod
    async def setup(self) -> None:
        """Set the TCP connection up."""

    @abstractmethod
    async def teardown(self) -> None:
        """Tear the TCP connection down."""

    @abstractmethod
    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """
        Select the destination, given the envelope.

        :param envelope: the envelope to be sent.
        :return: the stream writer to communicate with the recipient. None if it cannot be determined.
        """

    async def connect(self) -> None:
        """Set up the connection."""
        if self.is_connected:  # pragma: nocover
            self.logger.warning("Connection already set up.")
            return

        self.state = ConnectionStates.connecting
        try:
            await self.setup()
            self.state = ConnectionStates.connected
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.error(str(e))
            self.state = ConnectionStates.disconnected

    async def disconnect(self) -> None:
        """Tear down the connection."""
        if self.is_disconnected:  # pragma: nocover
            self.logger.warning("Connection already disconnected.")
            return

        self.state = ConnectionStates.disconnecting
        await self.teardown()
        self.state = ConnectionStates.disconnected

    async def _recv(self, reader: StreamReader) -> Optional[bytes]:
        """Receive bytes."""
        data = await reader.read(len(struct.pack("I", 0)))
        if not self.is_connected:
            return None
        nbytes = struct.unpack("I", data)[0]
        nbytes_read = 0
        data = b""
        while nbytes_read < nbytes:
            data += await reader.read(nbytes - nbytes_read)
            nbytes_read = len(data)
        return data

    async def _send(self, writer: StreamWriter, data: bytes) -> None:
        self.logger.debug("[{}] Send a message".format(self.address))
        nbytes = struct.pack("I", len(data))
        self.logger.debug("#bytes: {!r}".format(nbytes))
        try:
            writer.write(nbytes)
            writer.write(data)
            await writer.drain()
        except CancelledError:
            return None

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        self._ensure_valid_envelope_for_external_comms(envelope)
        writer = self.select_writer_from_envelope(envelope)
        if writer is not None:
            data = envelope.encode()
            await self._send(writer, data)
        else:
            self.logger.error(
                "[{}]: Cannot send envelope {}".format(self.address, envelope)
            )

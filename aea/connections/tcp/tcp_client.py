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

"""Implementation of the TCP client."""
import asyncio
import logging
import struct
from asyncio import StreamWriter, StreamReader, CancelledError
from typing import Optional, cast

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.connections.tcp.base import TCPConnection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPClientConnection(TCPConnection):
    """This class implements a TCP client."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int,
                 connection_id: str = "tcp_client",
                 **kwargs):
        """
        Initialize a TCP channel.

        :param public_key: public key.
        :param host: the socket bind address.
        :param port: the socket bind port.
        :param connection_id: the identifier for the connection object.
        """
        super().__init__(public_key, host, port, connection_id, **kwargs)

        self._reader, self._writer = (None, None)  # type: Optional[StreamReader], Optional[StreamWriter]

    async def setup(self):
        """Set the connection up."""
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
        public_key_bytes = self.public_key.encode("utf-8")
        await self._send(self._writer, public_key_bytes)

    async def teardown(self):
        """Tear the connection down."""
        if self._reader:
            self._reader.feed_eof()
        self._writer.close()

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope.

        :return: the received envelope, or None if an error occurred.
        """
        try:
            assert self._reader is not None
            data = await self._recv(self._reader)
            if data is None:
                logger.debug("[{}] No data received.".format(self.public_key))
                return None
            logger.debug("[{}] Message received: {!r}".format(self.public_key, data))
            envelope = Envelope.decode(data)  # TODO handle decoding error
            logger.debug("[{}] Decoded envelope: {}".format(self.public_key, envelope))
            return envelope
        except CancelledError:
            logger.debug("[{}] Read cancelled.".format(self.public_key))
            return None
        except struct.error as e:
            logger.debug("Struct error: {}".format(str(e)))
            return None
        except Exception as e:
            logger.exception(e)
            raise

    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """Select the destination, given the envelope."""
        return self._writer

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the TCP server connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        address = cast(str, connection_configuration.config.get("address"))
        port = cast(int, connection_configuration.config.get("port"))
        return TCPClientConnection(public_key, address, port,
                                   connection_id=connection_configuration.config.get("name"),
                                   restricted_to_protocols=set(connection_configuration.restricted_to_protocols))

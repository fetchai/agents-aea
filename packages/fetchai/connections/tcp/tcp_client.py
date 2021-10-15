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
from asyncio import (  # pylint: disable=unused-import
    CancelledError,
    StreamReader,
    StreamWriter,
)
from typing import Any, Optional, cast

from aea.configurations.base import ConnectionConfig
from aea.mail.base import Envelope

from packages.fetchai.connections.tcp.base import TCPConnection


_default_logger = logging.getLogger("aea.packages.fetchai.connections.tcp.tcp_client")

STUB_DIALOGUE_ID = 0


class TCPClientConnection(TCPConnection):
    """This class implements a TCP client."""

    def __init__(self, configuration: ConnectionConfig, **kwargs: Any) -> None:
        """
        Initialize a TCP client connection.

        :param configuration: the configuration object.
        :param kwargs: keyword arguments.
        """
        address = cast(str, configuration.config.get("address"))
        port = cast(int, configuration.config.get("port"))
        if address is None or port is None:
            raise ValueError("address and port must be set!")  # pragma: nocover
        super().__init__(address, port, configuration=configuration, **kwargs)
        self._reader, self._writer = (
            None,
            None,
        )  # type: Optional[StreamReader], Optional[StreamWriter]

    async def setup(self) -> None:
        """Set the connection up."""
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
        address_bytes = self.address.encode("utf-8")
        await self._send(self._writer, address_bytes)

    async def teardown(self) -> None:
        """Tear the connection down."""
        if self._reader is not None:
            self._reader.feed_eof()
        if self._writer is None:  # pragma: nocover
            return
        if self._writer.can_write_eof():
            self._writer.write_eof()
        await self._writer.drain()
        self._writer.close()
        # it should be 'await self._writer.wait_closed()'
        # however, it is not backward compatible with Python 3.6.
        # this turned out to work in the tests
        await asyncio.sleep(0.0)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the received envelope, or None if an error occurred.
        """
        try:
            if self._reader is None:
                raise ValueError("Reader not set.")  # pragma: nocover
            data = await self._recv(self._reader)
            if data is None:  # pragma: nocover
                self.logger.debug("[{}] No data received.".format(self.address))
                return None
            self.logger.debug("[{}] Message received: {!r}".format(self.address, data))
            envelope = Envelope.decode(data)
            self.logger.debug(
                "[{}] Decoded envelope: {}".format(self.address, envelope)
            )
            return envelope
        except CancelledError:
            self.logger.debug("[{}] Read cancelled.".format(self.address))
            return None
        except struct.error as e:
            self.logger.debug("Struct error: {}".format(str(e)))
            return None
        except Exception as e:
            self.logger.exception(e)
            raise

    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """Select the destination, given the envelope."""
        return self._writer

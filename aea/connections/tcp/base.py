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
import asyncio
import logging
import queue
import struct
import threading
from abc import ABC, abstractmethod
from asyncio import CancelledError, StreamWriter, StreamReader, AbstractEventLoop, Future
from concurrent.futures import Executor, ThreadPoolExecutor
from threading import Thread
from typing import Optional

from aea.connections.base import Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class TCPConnection(Connection, ABC):
    """Abstract TCP connection."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int):
        """Initialize the TCP connection."""
        super().__init__(type(self).__name__)
        self.public_key = public_key

        self.host = host
        self.port = port

        self._lock = threading.Lock()
        self._stopped = True
        self._connected = False

    def _run_task(self, coro):
        return asyncio.run_coroutine_threadsafe(coro=coro, loop=self._loop)

    @abstractmethod
    async def setup(self):
        """Set the TCP connection up."""

    @abstractmethod
    async def teardown(self):
        """Tear the TCP connection down."""

    @abstractmethod
    def select_writer_from_envelope(self, envelope: Envelope) -> Optional[StreamWriter]:
        """
        Select the destination, given the envelope.

        :param envelope: the envelope to be sent.
        :return: the stream writer to communicate with the recipient. None if it cannot be determined.
        """

    @property
    def is_established(self):
        """Check if the connection is established."""
        return not self._stopped and self._connected

    async def connect(self):
        """
        Set up the connection.

        :return: A queue or None.
        :raises ConnectionError: if a problem occurred during the connection.
        """
        with self._lock:
            try:
                if self.is_established:
                    logger.warning("Connection already set up.")
                    return

                self._stopped = False
                await self.setup()
                self._connected = True
            except Exception as e:
                logger.error(str(e))
                self._connected = False
                self._stopped = True

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """
        with self._lock:
            if not self.is_established:
                logger.warning("Connection is not set up.")
                return

            self._connected = False
            await self.teardown()
            self._stopped = True

    async def _recv(self, reader: StreamReader) -> Optional[bytes]:
        """Receive bytes."""
        data = await reader.read(len(struct.pack("I", 0)))
        if not self._connected:
            return None
        nbytes = struct.unpack("I", data)[0]
        nbytes_read = 0
        data = b""
        while nbytes_read < nbytes:
            data += (await reader.read(nbytes - nbytes_read))
            nbytes_read = len(data)
        return data

    async def _send(self, writer, data):
        logger.debug("[{}] Send a message".format(self.public_key))
        nbytes = struct.pack("I", len(data))
        logger.debug("#bytes: {!r}".format(nbytes))
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
        :return: None.
        """
        writer = self.select_writer_from_envelope(envelope)
        if writer is not None:
            data = envelope.encode()
            await self._send(writer, data)
        else:
            logger.error("[{}]: Cannot send envelope {}".format(self.public_key, envelope))


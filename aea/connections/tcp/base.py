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
import struct
import threading
from abc import ABC, abstractmethod
from asyncio import CancelledError, StreamWriter, StreamReader, Queue, transports, AbstractEventLoop
from threading import Thread
from typing import Optional, Protocol

from aea.connections.base import Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class AEAStreamProtocol(Protocol):
    """A simple stream protocol for AEAs."""

    def __init__(self, queue: Queue):
        """
        Initialize a protocol object.

        :param queue: the queue that stores incoming messages.
        """
        self.queue = queue

    def connection_made(self, transport: transports.BaseTransport) -> None:
        """Validate the connection made."""

    def data_received(self, data: bytes) -> None:
        """Handle the received data."""

    def eof_received(self) -> Optional[bool]:
        """Handle the end of the connection."""


class TCPConnection(Connection, ABC):
    """Abstract TCP connection."""

    def __init__(self,
                 public_key: str,
                 host: str,
                 port: int,
                 loop: Optional[AbstractEventLoop] = None):
        """Initialize the TCP connection."""
        super().__init__()
        self.public_key = public_key

        self.host = host
        self.port = port
        self._loop = asyncio.new_event_loop() if loop is None else loop

        self._lock = threading.Lock()
        self._stopped = True
        self._connected = False
        self._thread_loop = None  # type: Optional[Thread]

    def _run_task(self, coro):
        assert self._loop.is_running()
        return asyncio.run_coroutine_threadsafe(coro=coro, loop=self._loop)

    @property
    def _is_threaded(self) -> bool:
        """Check if the loop is run by our thread or from another thread."""
        return self._loop.is_running() and self._thread_loop is None

    def _start_loop(self):
        assert self._thread_loop is None
        self._thread_loop = Thread(target=self._loop.run_forever)
        self._thread_loop.start()

    def _stop_loop(self):
        assert self._thread_loop.is_alive()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread_loop.join(timeout=10)
        self._thread_loop = None

    @abstractmethod
    def setup(self):
        """Set the TCP connection up."""

    @abstractmethod
    def teardown(self):
        """Tear the TCP connection down."""

    @abstractmethod
    def select_writer_from_envelope(self, envelope: Envelope) -> StreamWriter:
        """Select the destination, given the envelope"""

    @property
    def is_established(self):
        """Check if the connection is established."""
        return not self._stopped and self._connected

    def connect(self):
        """
        Set up the connection.

        :return: A queue or None.
        """
        with self._lock:
            if self.is_established:
                logger.warning("Connection already set up.")
                return

            self._stopped = False
            if not self._is_threaded:
                self._start_loop()
            self.setup()
            self._connected = True

    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """
        with self._lock:
            if not self.is_established:
                logger.warning("Connection is not set up.")
                return

            self._connected = False
            self.teardown()
            if not self._is_threaded:
                self._stop_loop()
            self._stopped = True

    async def _recv(self, reader: StreamReader) -> Optional[bytes]:
        """Receive bytes."""
        try:
            data = await reader.read(len(struct.pack("I", 0)))
            nbytes = struct.unpack("I", data)[0]
            nbytes_read = 0
            data = b""
            while nbytes_read < nbytes:
                data += (await reader.read(nbytes - nbytes_read))
                nbytes_read = len(data)

            return data
        except CancelledError:
            return None
        except Exception as e:
            logger.exception(e)
            return None

    async def _send(self, writer: StreamWriter, data: bytes) -> None:
        """Send bytes."""
        logger.debug("Send a message")
        nbytes = struct.pack("I", len(data))
        logger.debug("#bytes: {!r}".format(nbytes))
        try:
            writer.write(nbytes)
            writer.write(data)
            await writer.drain()
        except CancelledError:
            return None

    async def _recv_loop(self, reader) -> None:
        """Process incoming messages."""
        try:
            if not self.is_established:
                logger.debug("Stopped receiving loop.")
                return
            logger.debug("Waiting for next message...")
            data = await self._recv(reader)
            if data is None:
                return
            logger.debug("Message received: {!r}".format(data))
            envelope = Envelope.decode(data)  # TODO handle decoding error
            logger.debug("Decoded envelope: {}".format(envelope))
            self.in_queue.put_nowait(envelope)
            await self._recv_loop(reader)
        except Exception as e:
            logger.exception(e)
            return

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        writer = self.select_writer_from_envelope(envelope)
        future = self._run_task(self._send(writer, envelope.encode()))
        future.result()  # TODO avoid waiting and handle cancellation
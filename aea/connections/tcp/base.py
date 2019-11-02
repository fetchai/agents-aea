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
                 port: int,
                 loop: Optional[AbstractEventLoop] = None,
                 executor: Optional[Executor] = None):
        """Initialize the TCP connection."""
        super().__init__()
        self.public_key = public_key

        self.host = host
        self.port = port
        self._loop = asyncio.new_event_loop() if loop is None else loop
        self._executor = executor if executor is not None else ThreadPoolExecutor()

        self._lock = threading.Lock()
        self._stopped = True
        self._connected = False
        self._thread_loop = None  # type: Optional[Thread]
        self._recv_task = None  # type: Optional[Future]
        self._fetch_task = None  # type: Optional[Future]

    def _run_task(self, coro):
        return asyncio.run_coroutine_threadsafe(coro=coro, loop=self._loop)

    @property
    def _is_threaded(self) -> bool:
        """Check if the loop is run by our thread or from another thread."""
        return self._loop.is_running() and self._thread_loop is None

    def _start_loop(self):
        assert self._thread_loop is None

        def loop_in_thread(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
            loop.close()

        self._thread_loop = Thread(target=loop_in_thread, args=(self._loop, ))
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

    def connect(self):
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
                if not self._is_threaded:
                    self._start_loop()

                self.setup()

                self._connected = True
            except Exception as e:
                logger.error(str(e))
                if not self._is_threaded:
                    self._stop_loop()
                self._connected = False
                self._stopped = True

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
            if not self._connected:
                return None
            nbytes = struct.unpack("I", data)[0]
            nbytes_read = 0
            data = b""
            while nbytes_read < nbytes:
                data += (await reader.read(nbytes - nbytes_read))
                nbytes_read = len(data)
            return data
        except CancelledError:
            logger.debug("[{}] Read cancelled.".format(self.public_key))
            return None
        except struct.error as e:
            logger.debug("Struct error: {}".format(str(e)))
            return None
        except Exception as e:
            logger.exception(e)
            raise

    async def _send(self, writer: StreamWriter, data: bytes) -> None:
        """Send bytes."""
        logger.debug("[{}] Send a message".format(self.public_key))
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
            logger.debug("[{}]: Waiting for receiving next message...".format(self.public_key))
            data = await self._recv(reader)
            if data is None:
                return
            logger.debug("[{}] Message received: {!r}".format(self.public_key, data))
            envelope = Envelope.decode(data)  # TODO handle decoding error
            logger.debug("[{}] Decoded envelope: {}".format(self.public_key, envelope))
            self.in_queue.put_nowait(envelope)
            await self._recv_loop(reader)
        except CancelledError:
            logger.debug("[{}] Receiving loop cancelled.".format(self.public_key))
            return
        except Exception as e:
            logger.exception(e)
            return

    async def _send_loop(self):
        """Process outgoing messages."""
        try:
            logger.debug("[{}]: Waiting for sending next message...".format(self.public_key))
            envelope = await self._loop.run_in_executor(self._executor, self.out_queue.get, True)
            if envelope is None:
                logger.debug("[{}] Stopped sending loop.".format(self.public_key))
                return
            writer = self.select_writer_from_envelope(envelope)
            await self._send(writer, envelope.encode())
            await self._send_loop()
        except CancelledError:
            logger.debug("[{}] Sending loop cancelled.".format(self.public_key))
            return
        except queue.Empty:
            await self._send_loop()
        except Exception as e:
            logger.exception(e)
            return

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        self.out_queue.put_nowait(envelope)

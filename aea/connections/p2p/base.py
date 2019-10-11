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
import queue
import struct
from abc import ABC
from asyncio import StreamReader, StreamWriter, CancelledError
from queue import Queue
from threading import Thread
from typing import Optional

from aea.connections.base import Channel, Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class TCPChannel(Channel, ABC):
    """Abstract TCP channel."""

    def __init__(self, public_key: str):
        """Initialize a TCP Channel."""
        self.in_queue = Queue()  # type: Queue
        self.public_key = public_key
        self._stopped = False

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
        logger.debug("#bytes: {}".format(nbytes))
        try:
            writer.write(nbytes)
            writer.write(data)
            await writer.drain()
        except CancelledError:
            return None

    async def _recv_loop(self, reader) -> None:
        """Process incoming messages."""
        try:
            if self._stopped:
                logger.debug("Stopped receiving loop.")
                return
            logger.debug("Waiting for next message...")
            data = await self._recv(reader)
            if data is None:
                return
            logger.debug("Message received: {}".format(data))
            envelope = Envelope.decode(data)  # TODO handle decoding error
            logger.debug("Decoded envelope: {}".format(envelope))
            self.in_queue.put_nowait(envelope)
            await self._recv_loop(reader)
        except Exception as e:
            logger.exception(e)
            return

    def recv(self, block=True, timeout=None) -> Optional[Envelope]:
        """Receive an envelope."""
        try:
            return self.in_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None


class TCPConnection(Connection, ABC):
    """Abstract TCP connection."""

    _channel: TCPChannel

    def __init__(self, public_key: str, channel: TCPChannel):
        """
        Initialize a TCP connection.

        :param public_key: the public key.
        :param channel: the TCP channel.
        """
        super().__init__()

        self.public_key = public_key
        self._channel = channel
        self._stopped = True

    def _fetch(self) -> None:
        """Fetch the envelopes from the outqueue and send them."""
        while not self._stopped:
            try:
                msg = self.out_queue.get(block=True, timeout=2.0)
                if msg is not None:
                    self.send(msg)
            except queue.Empty:
                pass

    def _receive_loop(self):
        """Receive envelopes."""
        while not self._stopped:
            try:
                data = self._channel.recv(block=True, timeout=2.0)
                if data is not None:
                    self.in_queue.put_nowait(data)
            except queue.Empty:
                pass

    @property
    def is_established(self) -> bool:
        """Return True if the connection has been established, False otherwise."""
        return not self._stopped

    def connect(self):
        """Connect to the local OEF Node."""
        if self._stopped:
            self._stopped = False
            self._channel.connect()
            self.in_thread = Thread(target=self._receive_loop)
            self.out_thread = Thread(target=self._fetch)
            self.in_thread.start()
            self.out_thread.start()

    def disconnect(self):
        """Disconnect from the local OEF Node."""
        if not self._stopped:
            self._stopped = True
            self._channel.disconnect()
            self.in_thread.join()
            self.out_thread.join()
            self.in_thread = None
            self.out_thread = None

    def send(self, envelope: Envelope):
        """Send a message."""
        if not self.is_established:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self._channel.send(envelope)

    def stop(self):
        """Tear down the connection."""
        self._channel.disconnect()

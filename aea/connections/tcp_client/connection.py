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
import queue
import struct
from asyncio import AbstractEventLoop, StreamReader, StreamWriter, Task, AbstractServer, transports
from ipaddress import IPv4Address
from threading import Thread
from typing import Dict, Optional, Tuple

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Channel, Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)

STUB_DIALOGUE_ID = 0


class TCPClientChannel(Channel):
    """Channel implementation for the local node."""

    def __init__(self, address: str, unix: bool = True, loop: Optional[AbstractEventLoop] = None):
        """
        Initialize a TCP channel.

        :param address: the socket bind address.
        :param unix: whether it's a unix server or a networked.
        :param loop: the asyncio loop.
        """
        self.in_queue = queue.Queue()
        self.address = address
        self.unix = unix
        self._loop = asyncio.new_event_loop() if loop is None else loop
        self._thread = None  # type: Optional[Thread]

        self._reader, self._writer = (None, None)

    async def _recv(self):
        data = await self._reader.read(len(struct.pack("I", 0)))
        nbytes = struct.unpack("I", data)[0]
        nbytes_read = 0
        data = b""
        while nbytes_read < nbytes:
            data += (await self._reader.read(nbytes - nbytes_read))
            nbytes_read = len(data)

        return data

    async def _send(self, data: bytes):
        nbytes = struct.pack("I", len(data))
        await self._writer.write(nbytes)
        await self._writer.write(data)
        await self._writer.drain()

    async def _recv_loop(self):
        data = await self._recv()
        envelope = Envelope.decode(data)
        self.in_queue.put_nowait(envelope)
        await self._recv_loop()

    def connect(self):
        """
        Set up the connection.

        :return: A queue or None.
        """
        self._thread = Thread(target=self._loop.run_forever)
        self._thread.start()

        if self.unix:
            coro = asyncio.open_unix_connection(path=self.address, loop=self._loop)
        else:
            ip, port = self.address.split(":")
            port = int(port)
            coro = asyncio.open_connection(ip, port, loop=self._loop, start_serving=False)
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        self._reader, self._writer = future.result()


    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """
        self._reader.close()
        self._writer.close()
        self._loop.stop()

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        asyncio.run_coroutine_threadsafe(self._send(envelope.encode()), loop=self._loop)

    def recv(self, block=True, timeout=None) -> Optional[Envelope]:
        """Receive an envelope."""
        try:
            self.in_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None


class TCPClientConnection(Connection):
    """Implementation of a TCP server connection."""

    def __init__(self, address: str):
        """
        Initialize a TCP connection

        :param address: the address
        """
        super().__init__()
        self.address = address

        self._stopped = True
        self._channel = TCPClientChannel(self.address, unix=True)

    def _fetch(self) -> None:
        """
        Fetch the messages from the outqueue and send them.

        :return: None
        """
        while not self._stopped:
            try:
                msg = self.out_queue.get(block=True, timeout=2.0)
                self.send(msg)
            except queue.Empty:
                pass

    def _receive_loop(self):
        """Receive messages."""
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

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """Get the Local OEF connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        return TCPClientConnection(connection_configuration.config.get("address"))

#!/usr/bin/env python3
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
"""Portable pipe implementation for Linux, MacOS, and Windows."""
import asyncio
import errno
import logging
import os
import socket
import struct
import tempfile
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from asyncio.streams import StreamWriter
from shutil import rmtree
from typing import IO, Optional

from aea.exceptions import enforce


_default_logger = logging.getLogger(__name__)

PIPE_CONN_TIMEOUT = 10.0
PIPE_CONN_ATTEMPTS = 10

TCP_SOCKET_PIPE_CLIENT_CONN_ATTEMPTS = 5


class IPCChannelClient(ABC):
    """Multi-platform interprocess communication channel for the client side."""

    @abstractmethod
    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Connect to communication channel

        :param timeout: timeout for other end to connect
        :return: connection status
        """

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """
        Write `data` bytes to the other end of the channel

        Will first write the size than the actual data

        :param data: bytes to write
        """

    @abstractmethod
    async def read(self) -> Optional[bytes]:
        """
        Read bytes from the other end of the channel

        Will first read the size than the actual data

        :return: read bytes
        """

    @abstractmethod
    async def close(self) -> None:
        """Close the communication channel."""


class IPCChannel(IPCChannelClient):
    """Multi-platform interprocess communication channel."""

    @property
    @abstractmethod
    def in_path(self) -> str:
        """
        Rendezvous point for incoming communication.

        :return: path
        """

    @property
    @abstractmethod
    def out_path(self) -> str:
        """
        Rendezvous point for outgoing communication.

        :return: path
        """


class PosixNamedPipeProtocol:
    """Posix named pipes async wrapper communication protocol."""

    def __init__(
        self,
        in_path: str,
        out_path: str,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """
        Initialize a new posix named pipe.

        :param in_path: rendezvous point for incoming data
        :param out_path: rendezvous point for outgoing data
        :param logger: the logger
        :param loop: the event loop
        """

        self.logger = logger
        self._loop = loop
        self._in_path = in_path
        self._out_path = out_path
        self._in = -1
        self._out = -1

        self._stream_reader = None  # type: Optional[asyncio.StreamReader]
        self._reader_protocol = None  # type: Optional[asyncio.StreamReaderProtocol]
        self._fileobj = None  # type: Optional[IO[str]]

        self._connection_attempts = PIPE_CONN_ATTEMPTS
        self._connection_timeout = PIPE_CONN_TIMEOUT

    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Connect to the other end of the pipe

        :param timeout: timeout before failing
        :return: connection success
        """

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._connection_timeout = timeout / PIPE_CONN_ATTEMPTS if timeout > 0 else 0
        if self._connection_attempts <= 1:  # pragma: no cover
            return False
        self._connection_attempts -= 1

        self.logger.debug(
            "Attempt opening pipes {}, {}...".format(self._in_path, self._out_path)
        )

        self._in = os.open(self._in_path, os.O_RDONLY | os.O_NONBLOCK | os.O_SYNC)

        try:
            self._out = os.open(self._out_path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as e:  # pragma: no cover
            if e.errno == errno.ENXIO:
                self.logger.debug("Sleeping for {}...".format(self._connection_timeout))
                await asyncio.sleep(self._connection_timeout)
                return await self.connect(timeout)
            raise e

        # setup reader
        enforce(
            self._in != -1 and self._out != -1 and self._loop is not None,
            "Incomplete initialization.",
        )
        self._stream_reader = asyncio.StreamReader(loop=self._loop)
        self._reader_protocol = asyncio.StreamReaderProtocol(
            self._stream_reader, loop=self._loop
        )
        self._fileobj = os.fdopen(self._in, "r")
        await self._loop.connect_read_pipe(
            lambda: self.__reader_protocol, self._fileobj
        )

        return True

    @property
    def __reader_protocol(self) -> asyncio.StreamReaderProtocol:
        """Get reader protocol."""
        if self._reader_protocol is None:
            raise ValueError("reader protocol not set!")  # pragma: nocover
        return self._reader_protocol

    async def write(self, data: bytes) -> None:
        """
        Write to pipe.

        :param data: bytes to write to pipe
        """
        self.logger.debug("writing {}...".format(len(data)))
        size = struct.pack("!I", len(data))
        os.write(self._out, size + data)
        await asyncio.sleep(0.0)

    async def read(self) -> Optional[bytes]:
        """
        Read from pipe.

        :return: read bytes
        """
        if self._stream_reader is None:  # pragma: nocover
            raise ValueError("StreamReader not set, call connect first!")
        try:
            self.logger.debug("waiting for messages (in={})...".format(self._in_path))
            buf = await self._stream_reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
            if size <= 0:  # pragma: no cover
                return None
            data = await self._stream_reader.readexactly(size)
            if not data:  # pragma: no cover
                return None
            return data
        except asyncio.IncompleteReadError as e:  # pragma: no cover
            self.logger.info(
                "Connection disconnected while reading from pipe ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None
        except asyncio.CancelledError:  # pragma: no cover
            return None

    async def close(self) -> None:
        """Disconnect pipe."""
        self.logger.debug("closing pipe (in={})...".format(self._in_path))
        if self._fileobj is None:
            raise ValueError("Pipe not connected")  # pragma: nocover
        try:
            # hack for MacOSX
            size = struct.pack("!I", 0)
            os.write(self._out, size)

            os.close(self._out)
            self._fileobj.close()
        except OSError:  # pragma: no cover
            pass
        await asyncio.sleep(0)


class TCPSocketProtocol:
    """TCP socket communication protocol."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """
        Initialize the tcp socket protocol.

        :param reader: established asyncio reader
        :param writer: established asyncio writer
        :param logger: the logger
        :param loop: the event loop
        """

        self.logger = logger
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self._reader = reader
        self._writer = writer

    @property
    def writer(self) -> StreamWriter:
        """Get a writer associated with  protocol."""
        return self._writer

    async def write(self, data: bytes) -> None:
        """
        Write to socket.

        :param data: bytes to write
        """
        if self._writer is None:
            raise ValueError("writer not set!")  # pragma: nocover
        self.logger.debug("writing {}...".format(len(data)))
        size = struct.pack("!I", len(data))
        self._writer.write(size + data)
        await self._writer.drain()

    async def read(self) -> Optional[bytes]:
        """
        Read from socket.

        :return: read bytes
        """
        try:
            self.logger.debug("waiting for messages...")
            buf = await self._reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
            data = await self._reader.readexactly(size)
            if not data:  # pragma: no cover
                return None
            if len(data) != size:  # pragma: no cover
                raise ValueError(
                    f"Incomplete Read Error! Expected size={size}, got: {len(data)}"
                )
            return data
        except asyncio.IncompleteReadError as e:  # pragma: no cover
            self.logger.info(
                "Connection disconnected while reading from pipe ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None
        except asyncio.CancelledError:  # pragma: no cover
            return None

    async def close(self) -> None:
        """Disconnect socket."""
        if self._writer.can_write_eof():
            self._writer.write_eof()
        await self._writer.drain()
        self._writer.close()
        wait_closed = getattr(self._writer, "wait_closed", None)
        if wait_closed:
            # in py3.6 writer does not have the coroutine
            await wait_closed()  # pragma: nocover


class TCPSocketChannel(IPCChannel):
    """Interprocess communication channel implementation using tcp sockets."""

    def __init__(
        self,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """Initialize tcp socket interprocess communication channel."""
        self.logger = logger
        self._loop = loop
        self._server = None  # type: Optional[asyncio.AbstractServer]
        self._connected = None  # type: Optional[asyncio.Event]
        self._sock = None  # type: Optional[TCPSocketProtocol]

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        self._port = s.getsockname()[1]
        s.close()

    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Setup communication channel and wait for other end to connect.

        :param timeout: timeout for the connection to be established
        :return: connection status
        """

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._connected = asyncio.Event()
        self._server = await asyncio.start_server(
            self._handle_connection, host="127.0.0.1", port=self._port
        )
        if self._server.sockets is None:
            raise ValueError("Server sockets is None!")  # pragma: nocover
        self._port = self._server.sockets[0].getsockname()[1]
        self.logger.debug("socket pipe rdv point: {}".format(self._port))

        try:
            await asyncio.wait_for(self._connected.wait(), timeout)
        except asyncio.TimeoutError:  # pragma: no cover
            return False

        self._server.close()
        await self._server.wait_closed()

        return True

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle connection."""
        if self._connected is None:
            raise ValueError("Connected is None!")  # pragma: nocover
        self._connected.set()
        self._sock = TCPSocketProtocol(
            reader, writer, logger=self.logger, loop=self._loop
        )

    async def write(self, data: bytes) -> None:
        """
        Write to channel.

        :param data: bytes to write
        """
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        await self._sock.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read from channel.

        :return: read bytes
        """
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        return await self._sock.read()

    async def close(self) -> None:
        """Disconnect from channel and clean it up."""
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        await self._sock.close()

    @property
    def in_path(self) -> str:
        """Rendezvous point for incoming communication."""
        return str(self._port)

    @property
    def out_path(self) -> str:
        """Rendezvous point for outgoing communication."""
        return str(self._port)


class PosixNamedPipeChannel(IPCChannel):
    """Interprocess communication channel implementation using Posix named pipes."""

    def __init__(
        self,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """Initialize posix named pipe interprocess communication channel."""
        self.logger = logger
        self._loop = loop

        self._pipe_dir = tempfile.mkdtemp()
        self._in_path = "{}/process_to_aea".format(self._pipe_dir)
        self._out_path = "{}/aea_to_process".format(self._pipe_dir)

        # setup fifos
        self.logger.debug(
            "Creating pipes ({}, {})...".format(self._in_path, self._out_path)
        )
        if os.path.exists(self._in_path):
            os.remove(self._in_path)  # pragma: no cover
        if os.path.exists(self._out_path):
            os.remove(self._out_path)  # pragma: no cover
        os.mkfifo(self._in_path)
        os.mkfifo(self._out_path)

        self._pipe = PosixNamedPipeProtocol(
            self._in_path, self._out_path, logger=logger, loop=loop
        )

    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Setup communication channel and wait for other end to connect.

        :param timeout: timeout for connection to be established
        :return: bool, indicating success
        """

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        return await self._pipe.connect(timeout)

    async def write(self, data: bytes) -> None:
        """
        Write to the channel.

        :param data: data to write to channel
        """
        await self._pipe.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read from the channel.

        :return: read bytes
        """
        return await self._pipe.read()

    async def close(self) -> None:
        """Close the channel and clean it up."""
        await self._pipe.close()
        rmtree(self._pipe_dir)

    @property
    def in_path(self) -> str:
        """Rendezvous point for incoming communication."""
        return self._in_path

    @property
    def out_path(self) -> str:
        """Rendezvous point for outgoing communication."""
        return self._out_path


class TCPSocketChannelClient(IPCChannelClient):
    """Interprocess communication channel client using tcp sockets."""

    def __init__(  # pylint: disable=unused-argument
        self,
        in_path: str,
        out_path: str,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """
        Initialize a tcp socket communication channel client.

        :param in_path: rendezvous point for incoming data
        :param out_path: rendezvous point for outgoing data
        :param logger: the logger
        :param loop: the event loop
        """
        self.logger = logger
        self._loop = loop
        parts = in_path.split(":")
        if len(parts) == 1:
            self._port = int(in_path)
            self._host = "127.0.0.1"
        else:  # pragma: nocover
            self._port = int(parts[1])
            self._host = parts[0]
        self._sock = None  # type: Optional[TCPSocketProtocol]

        self._attempts = TCP_SOCKET_PIPE_CLIENT_CONN_ATTEMPTS
        self._timeout = PIPE_CONN_TIMEOUT / self._attempts
        self.last_exception: Optional[Exception] = None

    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Connect to the other end of the communication channel.

        :param timeout: timeout for connection to be established
        :return: connection status
        """
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._timeout = timeout / TCP_SOCKET_PIPE_CLIENT_CONN_ATTEMPTS

        self.logger.debug(
            "Attempting to connect to {}:{}.....".format("127.0.0.1", self._port)
        )

        connected = False
        while self._attempts > 0:
            self._attempts -= 1
            try:
                self._sock = await self._open_connection()
                connected = True
                break
            except ConnectionRefusedError:
                await asyncio.sleep(self._timeout)
            except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
                self.last_exception = e
                return False

        return connected

    async def _open_connection(self) -> TCPSocketProtocol:
        reader, writer = await asyncio.open_connection(
            self._host, self._port, loop=self._loop,  # pylint: disable=protected-access
        )
        return TCPSocketProtocol(reader, writer, logger=self.logger, loop=self._loop)

    async def write(self, data: bytes) -> None:
        """
        Write data to channel.

        :param data: bytes to write
        """
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        await self._sock.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read data from channel.

        :return: read bytes
        """
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        return await self._sock.read()

    async def close(self) -> None:
        """Disconnect from communication channel."""
        if self._sock is None:
            raise ValueError("Socket pipe not connected.")  # pragma: nocover
        await self._sock.close()


class PosixNamedPipeChannelClient(IPCChannelClient):
    """Interprocess communication channel client using Posix named pipes."""

    def __init__(
        self,
        in_path: str,
        out_path: str,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """
        Initialize a posix named pipe communication channel client.

        :param in_path: rendezvous point for incoming data
        :param out_path: rendezvous point for outgoing data
        :param logger: the logger
        :param loop: the event loop
        """

        self.logger = logger
        self._loop = loop

        self._in_path = in_path
        self._out_path = out_path
        self._pipe = None  # type: Optional[PosixNamedPipeProtocol]
        self.last_exception: Optional[Exception] = None

    async def connect(self, timeout: float = PIPE_CONN_TIMEOUT) -> bool:
        """
        Connect to the other end of the communication channel.

        :param timeout: timeout for connection to be established
        :return: connection status
        """

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._pipe = PosixNamedPipeProtocol(
            self._in_path, self._out_path, logger=self.logger, loop=self._loop
        )
        try:
            return await self._pipe.connect()
        except Exception as e:  # pragma: nocover  # pylint: disable=broad-except
            self.last_exception = e
            return False

    async def write(self, data: bytes) -> None:
        """
        Write data to channel.

        :param data: bytes to write
        """
        if self._pipe is None:
            raise ValueError("Pipe not connected.")  # pragma: nocover
        await self._pipe.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read data from channel.

        :return: read bytes
        """
        if self._pipe is None:
            raise ValueError("Pipe not connected.")  # pragma: nocover
        return await self._pipe.read()

    async def close(self) -> None:
        """Disconnect from communication channel."""
        if self._pipe is None:
            raise ValueError("Pipe not connected.")  # pragma: nocover
        return await self._pipe.close()


def make_ipc_channel(
    logger: logging.Logger = _default_logger, loop: Optional[AbstractEventLoop] = None
) -> IPCChannel:
    """
    Build a portable bidirectional InterProcess Communication channel

    :param logger: the logger
    :param loop: the loop
    :return: IPCChannel
    """
    if os.name == "posix":
        return PosixNamedPipeChannel(logger=logger, loop=loop)
    if os.name == "nt":  # pragma: nocover
        return TCPSocketChannel(logger=logger, loop=loop)
    raise NotImplementedError(  # pragma: nocover
        "make ipc channel is not supported on platform {}".format(os.name)
    )


def make_ipc_channel_client(
    in_path: str,
    out_path: str,
    logger: logging.Logger = _default_logger,
    loop: Optional[AbstractEventLoop] = None,
) -> IPCChannelClient:
    """
    Build a portable bidirectional InterProcess Communication client channel

    :param in_path: rendezvous point for incoming communication
    :param out_path: rendezvous point for outgoing outgoing
    :param logger: the logger
    :param loop: the loop
    :return: IPCChannel
    """
    if os.name == "posix":
        return PosixNamedPipeChannelClient(in_path, out_path, logger=logger, loop=loop)
    if os.name == "nt":  # pragma: nocover
        return TCPSocketChannelClient(in_path, out_path, logger=logger, loop=loop)
    raise NotImplementedError(  # pragma: nocover
        "make ip channel client is not supported on platform {}".format(os.name)
    )

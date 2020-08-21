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
from typing import IO, Optional

from aea.exceptions import enforce

_default_logger = logging.getLogger(__name__)

PIPE_CONN_TIMEOUT = 10.0
PIPE_CONN_ATTEMPTS = 10


class LocalPortablePipe(ABC):
    """
    Multi-platform interprocess communication channel
    """

    @abstractmethod
    async def connect(self, timeout=PIPE_CONN_TIMEOUT) -> bool:
        """
        Setup the communication channel with the other process
        """

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """
        Write `data` bytes to the other end of the channel
        Will first write the size than the actual data
        """

    @abstractmethod
    async def read(self) -> Optional[bytes]:
        """
        Read bytes from the other end of the channel
        Will first read the size than the actual data
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close the communication channel
        """

    @property
    @abstractmethod
    def in_path(self) -> str:
        """
        Returns the rendezvous point for incoming communication
        """

    @property
    @abstractmethod
    def out_path(self) -> str:
        """
        Returns the rendezvous point for outgoing communication
        """


class TCPSocketPipe(LocalPortablePipe):
    """
    Interprocess communication implementation using tcp sockets
    """

    def __init__(
        self,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ):
        self.logger = logger
        self._timeout = 0
        self._server = None  # type: Optional[asyncio.AbstractServer]
        self._connected = None  # type: Optional[asyncio.Event]
        self._reader = None  # type: Optional[asyncio.StreamReader]
        self._writer = None  # type: Optional[asyncio.StreamWriter]
        self._loop = loop if loop is not None else asyncio.get_event_loop()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        self._port = s.getsockname()[1]
        s.close()

    async def connect(self, timeout=PIPE_CONN_TIMEOUT) -> bool:
        self._connected = asyncio.Event()
        self._timeout = timeout if timeout > 0 else 0
        self._server = await asyncio.start_server(
            self._handle_connection, host="127.0.0.1", port=self._port
        )
        if self._server.sockets is None:
            raise ValueError("Sockets is not set on server.")
        self._port = self._server.sockets[0].getsockname()[1]
        self.logger.debug("socket pipe setup {}".format(self._port))

        try:
            await asyncio.wait_for(self._connected.wait(), self._timeout)
        except asyncio.TimeoutError:  # pragma: no cover
            return False

        self._server.close()
        await self._server.wait_closed()

        return True

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        if self._connected is None:
            raise ValueError("Not connected!")
        self._connected.set()
        self._reader = reader
        self._writer = writer

    async def write(self, data: bytes) -> None:
        if self._writer is None:
            raise ValueError("Writer not set.")
        size = struct.pack("!I", len(data))
        self._writer.write(size)
        self._writer.write(data)
        await self._writer.drain()

    async def read(self) -> Optional[bytes]:
        self.logger.debug("Reading pipes...")
        if self._reader is None:
            raise ValueError("Reader not set.")
        try:
            self.logger.debug("Waiting for messages...")
            buf = await self._reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
            data = await self._reader.readexactly(size)
            if not data:  # pragma: no cover
                return None
            return data
        except asyncio.IncompleteReadError as e:  # pragma: no cover
            self.logger.info(
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None

    async def close(self) -> None:
        if self._writer is None:
            raise ValueError("Writer not set.")
        self._writer.write_eof()
        await self._writer.drain()
        self._writer.close()

    @property
    def in_path(self) -> str:
        return str(self._port)

    @property
    def out_path(self) -> str:
        return str(self._port)


class PosixNamedPipe(LocalPortablePipe):
    """
    Interprocess communication implementation using Posix named pipes
    """

    def __init__(
        self,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
    ):
        self.logger = logger
        tmp_dir = tempfile.mkdtemp()
        self._in_path = "{}/process_to_aea".format(tmp_dir)
        self._out_path = "{}/aea_to_process".format(tmp_dir)
        self._in = -1
        self._out = -1
        self._loop = loop if loop is not None else asyncio.get_event_loop()

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

        self._stream_reader = None  # type: Optional[asyncio.StreamReader]
        self._log_file_desc = None  # type: Optional[IO[str]]
        self._reader_protocol = None  # type: Optional[asyncio.StreamReaderProtocol]
        self._fileobj = None  # type: Optional[IO[str]]

        self._connection_attempts = PIPE_CONN_ATTEMPTS
        self._connection_timeout = -1

    async def connect(self, timeout=PIPE_CONN_TIMEOUT) -> bool:
        self._connection_timeout = timeout / PIPE_CONN_ATTEMPTS if timeout > 0 else 0
        if self._connection_attempts <= 1:  # pragma: no cover
            return False
        self._connection_attempts -= 1

        self.logger.debug(
            "Attempt opening pipes {}, {}...".format(self._in_path, self._out_path)
        )

        self._in = os.open(self._in_path, os.O_RDONLY | os.O_NONBLOCK)

        try:
            self._out = os.open(self._out_path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as e:
            if e.errno == errno.ENXIO:
                self.logger.debug("Sleeping for {}...".format(self._connection_timeout))
                await asyncio.sleep(self._connection_timeout)
                return await self.connect(timeout)
            else:
                raise e  # pragma: no cover

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
            raise ValueError("reader protocol not set!")
        return self._reader_protocol

    async def write(self, data: bytes) -> None:
        """
        Write to the writer stream.

        :param data: data to write to stream
        """
        self.logger.debug("writing {}...".format(str(data)))
        size = struct.pack("!I", len(data))
        os.write(self._out, size)
        os.write(self._out, data)

    async def read(self) -> Optional[bytes]:
        """
        Read from the reader stream.

        :return: bytes
        """
        self.logger.debug("reading {}...".format(""))
        if self._stream_reader is None:
            raise ValueError("StreamReader not set, call connect first!")
        try:
            self.logger.debug("Waiting for messages...")
            buf = await self._stream_reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
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

    async def close(self) -> None:
        if self._fileobj is None:
            raise ValueError("Pipe not connected")
        self._fileobj.close()
        os.close(self._out)
        await asyncio.sleep(0)

    @property
    def in_path(self) -> str:
        return self._in_path

    @property
    def out_path(self) -> str:
        return self._out_path


def make_pipe(logger: logging.Logger = _default_logger) -> LocalPortablePipe:
    """
    Build a portable bidirectional Interprocess Communication Channel
    """

    if os.name == "posix":
        return PosixNamedPipe(logger=logger)
    elif os.name == "nt":  # pragma: nocover
        return TCPSocketPipe(logger=logger)
    else:  # pragma: nocover
        raise Exception("make pipe is not supported on platform {}".format(os.name))

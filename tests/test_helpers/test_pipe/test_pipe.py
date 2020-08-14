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

import asyncio
import os
import struct
from threading import Thread
from typing import IO, Optional, Union

import pytest

from aea.helpers.pipe import PosixNamedPipe, TCPSocketPipe, make_pipe

from tests.conftest import skip_test_windows

TCP_SOCKET_PIPE_CLIENT_CONN_ATTEMPTS = 5
TCP_SOCKET_PIPE_CLIENT_CONN_TIMEOUT = 0.1


class PosixNamedPipeClient:
    def __init__(self, in_path: str, out_path: str, loop=None):
        self._loop = loop

        self._in_path = in_path
        self._out_path = out_path
        self._in = -1
        self._out = -1

        self._reader_protocol = None  # type: Optional[asyncio.StreamReaderProtocol]
        self._stream_reader = None  # type: Optional[asyncio.StreamReader]
        self._fileobj = None  # type: Optional[IO[str]]

        print("PosixNamedPipe setup successfully")

    @property
    def __reader_protocol(self) -> asyncio.StreamReaderProtocol:
        """Get reader protocol."""
        assert self._reader_protocol is not None, "reader protocol not set!"
        return self._reader_protocol

    async def run_echo_service(self):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        print("PosixNamedPipe running echo service...")
        self._out = os.open(self._out_path, os.O_WRONLY)
        self._in = os.open(self._in_path, os.O_RDONLY)

        self._stream_reader = asyncio.StreamReader(loop=self._loop)
        self._reader_protocol = asyncio.StreamReaderProtocol(
            self._stream_reader, loop=self._loop
        )
        self._fileobj = os.fdopen(self._in, "r")
        await self._loop.connect_read_pipe(
            lambda: self.__reader_protocol, self._fileobj
        )

        while True:
            try:
                print("PosixNamedPipe waiting for messages...")
                buf = await self._stream_reader.readexactly(4)
                if not buf:  # pragma: no cover
                    break
                size = struct.unpack("!I", buf)[0]
                data = await self._stream_reader.readexactly(size)
                if not data:  # pragma: no cover
                    break

                size = struct.pack("!I", len(data))
                os.write(self._out, size)
                os.write(self._out, data)
                self._out.flush()
            except (asyncio.IncompleteReadError, asyncio.CancelledError):
                break
        print("PosixNamedPipe exiting...")


class TCPSocketPipeClient:
    def __init__(self, port: int, loop=None):
        self._loop = loop

        self._port = port
        self._reader = None  # type: Optional[asyncio.StreamReader]
        self._writer = None  # type: Optional[asyncio.StreamWriter]

        self._attempts = TCP_SOCKET_PIPE_CLIENT_CONN_ATTEMPTS

    async def run_echo_service(self):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        while self._attempts > 0:
            self._attempts -= 1
            try:
                self._reader, self._writer = await asyncio.open_connection(
                    "127.0.0.1",
                    self._port,  # pylint: disable=protected-access
                    loop=self._loop,
                )
                break
            except ConnectionRefusedError:
                await asyncio.sleep(TCP_SOCKET_PIPE_CLIENT_CONN_TIMEOUT)
                continue
            except (asyncio.IncompleteReadError, asyncio.CancelledError):
                return

        try:
            while True:
                buf = await self._reader.readexactly(4)
                if not buf:  # pragma: no cover
                    break
                size = struct.unpack("!I", buf)[0]
                data = await self._reader.readexactly(size)
                if not data:  # pragma: no cover
                    break

                size = struct.pack("!I", len(data))
                self._writer.write(size)
                self._writer.write(data)
                await self._writer.drain()

        except (asyncio.IncompleteReadError, asyncio.CancelledError):
            return


class PortablePipeClient:
    def __init__(self, in_path: str, out_path: str, loop=None):
        self._client_pipe = (
            None
        )  # type: Optional[Union[TCPSocketPipeClient, PosixNamedPipeClient]]
        if os.name == "posix":
            self._client_pipe = PosixNamedPipeClient(in_path, out_path, loop)
        elif os.name == "nt":
            self._client_pipe = TCPSocketPipeClient(int(in_path), loop)
        else:
            raise Exception(
                "PortablePipeClient is not supported on platform {}".format(os.name)
            )

        self._loop = loop

    def run(self):
        assert self._client_pipe is not None
        print("PortablePipeClient running...")
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._client_pipe.run_echo_service())


@pytest.mark.asyncio
class TestAEAHelperMakePipe:
    """Test that make_pipe utility and abstract class LocaPortablePipe work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        pipe = make_pipe()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "Pipe not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = PortablePipeClient(pipe.out_path, pipe.in_path)
        client = Thread(target=client_pipe.run)
        client.start()

        try:
            assert await connected, "Failed to connect pipe"

            message = b"hello"
            await pipe.write(message)
            received = await pipe.read()

            assert received == message, "Echoed message differs"

        except Exception:
            raise
        finally:
            await pipe.close()
            client.join()


@pytest.mark.asyncio
class TestAEAHelperTCPSocketPipe:
    """Test that TCPSocketPipe work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        pipe = TCPSocketPipe()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "TCPSocketPipe not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = TCPSocketPipeClient(int(pipe.in_path))

        def run_client_pipe():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(client_pipe.run_echo_service())

        client = Thread(target=run_client_pipe)
        client.start()

        try:
            assert await connected, "Failed to connect pipe"

            message = b"hello"
            await pipe.write(message)
            received = await pipe.read()

            assert received == message, "Echoed message differs"

        except Exception:
            raise
        finally:
            await pipe.close()
            client.join()


@skip_test_windows
@pytest.mark.asyncio
class TestAEAHelperPosixNamedPipe:
    """Test that TCPSocketPipe work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        pipe = PosixNamedPipe()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "PosixNamedPipe not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = PosixNamedPipeClient(pipe.out_path, pipe.in_path)

        def run_client_pipe():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(client_pipe.run_echo_service())

        client = Thread(target=run_client_pipe)
        client.start()

        try:
            assert await connected, "Failed to connect pipe"

            message = b"hello"
            await pipe.write(message)
            received = await pipe.read()

            assert received == message, "Echoed message differs"

        except Exception:
            raise
        finally:
            await pipe.close()
            client.join()

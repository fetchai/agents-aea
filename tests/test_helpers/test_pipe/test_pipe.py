# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Tests for the pipe module."""
import asyncio
from threading import Thread

import pytest

from aea.helpers.pipe import (
    IPCChannelClient,
    PosixNamedPipeChannel,
    PosixNamedPipeChannelClient,
    TCPSocketChannel,
    TCPSocketChannelClient,
    make_ipc_channel,
    make_ipc_channel_client,
)

from tests.conftest import skip_test_windows


def _run_echo_service(client: IPCChannelClient):
    async def echo_service(client: IPCChannelClient):
        try:
            await client.connect()
            while True:
                data = await client.read()
                if not data:
                    break
                await client.write(data)
        except (asyncio.IncompleteReadError, asyncio.CancelledError, OSError):
            pass
        finally:
            await client.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(echo_service(client))


@pytest.mark.asyncio
class TestAEAHelperMakePipe:
    """Test that make_ipc_channel utility and abstract class IPCChannel work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        """Test connection communication."""
        pipe = make_ipc_channel()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "Pipe not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = make_ipc_channel_client(pipe.out_path, pipe.in_path)

        client = Thread(target=_run_echo_service, args=[client_pipe])
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
class TestAEAHelperTCPSocketChannel:
    """Test that TCPSocketChannel work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        """Test connection communication."""
        pipe = TCPSocketChannel()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "TCPSocketChannel not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = TCPSocketChannelClient(pipe.out_path, pipe.in_path)

        client = Thread(target=_run_echo_service, args=[client_pipe])
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
    async def test_connection_refused(self):
        """Test connection refused."""
        pipe = TCPSocketChannel()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "TCPSocketChannel not properly setup"

        client_pipe = TCPSocketChannelClient(pipe.out_path, pipe.in_path)

        connected = await client_pipe.connect()
        assert connected is False


def make_future(result) -> asyncio.Future:
    """Make future for value."""
    f = asyncio.Future()  # type: ignore
    f.set_result(result)
    return f


@skip_test_windows
@pytest.mark.asyncio
class TestAEAHelperPosixNamedPipeChannel:
    """Test that TCPSocketChannel work properly"""

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        """Test connection communication."""
        pipe = PosixNamedPipeChannel()
        assert (
            pipe.in_path is not None and pipe.out_path is not None
        ), "PosixNamedPipeChannel not properly setup"

        connected = asyncio.ensure_future(pipe.connect())

        client_pipe = PosixNamedPipeChannelClient(pipe.out_path, pipe.in_path)

        client = Thread(target=_run_echo_service, args=[client_pipe])
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

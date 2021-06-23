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
"""Tests for the pipe module."""
import asyncio
from threading import Thread
from unittest.mock import MagicMock, patch

import pytest

from aea.helpers.pipe import (
    IPCChannelClient,
    PosixNamedPipeChannel,
    PosixNamedPipeChannelClient,
    TCPSocketChannel,
    TCPSocketChannelClient,
    TCPSocketChannelClientTLS,
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


@pytest.mark.asyncio
class TestAEAHelperTCPSocketChannelTLS:
    """Test that TCPSocketChannelTLS work properly"""

    SERVER_PUB_KEY = (
        "03e09d7febfc3e3ef4c38321fb10c4303956e65e1d03ead77470941e82428f80d2"
    )
    SIGNATURE = b"0D\x02 \x7f\xcf\xa7\xe9~\x1d{\xf1\xb6\"\x98\x1d'\xd2}\x13\xb5\x13\x0c,]}7\xf3\xa6G\x958q_\x89\x08\x02 >\x91\x9e!\xb5\x1f/\xe4\x0c\xab\x9ej\xb7~Z8\x0b\x06Et\x9f\x1b.SZ*Q\xb7\x13\x85\xaa-"
    SESSION_KEY = b"\x04D\x08\xe1\xca\xfc;\x01(\x0f\xb9&\x92\x12\xe6\x0b\x02\xdc\x082\xa3\xff\x05\x1f#\xeaK\xd3!\xf5\xcc\xcf\x86\x98\x17g\x80_\xc7o;\x9e\x86,O\xbd\xa1bO\x06\x92\x85\x94\x9f\xbf}\xc2\xdd[\xe6AI\x9a\x9c\x92"

    @pytest.mark.asyncio
    async def test_connection_communication(self):
        """Test connection communication."""
        client_pipe = TCPSocketChannelClientTLS(
            "localhost:11111", "", server_pub_key=self.SERVER_PUB_KEY
        )

        with patch(
            "asyncio.open_connection",
            MagicMock(return_value=make_future((MagicMock(), MagicMock()))),
        ), patch(
            "aea.helpers.pipe.TCPSocketProtocol.read",
            MagicMock(return_value=make_future(self.SIGNATURE)),
        ), patch.object(
            client_pipe, "_get_session_pub_key", return_value=self.SESSION_KEY
        ):
            await client_pipe._open_connection()


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

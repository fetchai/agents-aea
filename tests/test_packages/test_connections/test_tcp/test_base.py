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

"""This module contains the tests for the TCP base module."""

import asyncio
import unittest.mock
from asyncio import CancelledError

import pytest

from aea.mail.base import Envelope

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import (
    _make_tcp_client_connection,
    _make_tcp_server_connection,
    get_unused_tcp_port,
)


@pytest.mark.asyncio
async def test_connect_twice():
    """Test that connecting twice the tcp connection works correctly."""
    port = get_unused_tcp_port()
    tcp_connection = _make_tcp_server_connection(
        "address", "public_key", "127.0.0.1", port
    )

    await tcp_connection.connect()
    await asyncio.sleep(0.1)
    with unittest.mock.patch.object(tcp_connection.logger, "warning") as mock_logger:
        await tcp_connection.connect()
        mock_logger.assert_called_with("Connection already set up.")

    await tcp_connection.disconnect()


@pytest.mark.asyncio
async def test_connect_raises_exception():
    """Test the case that a connection attempt raises an exception."""
    port = get_unused_tcp_port()
    tcp_connection = _make_tcp_server_connection(
        "address", "public_key", "127.0.0.1", port
    )

    with unittest.mock.patch.object(tcp_connection.logger, "error") as mock_logger:
        with unittest.mock.patch.object(
            tcp_connection, "setup", side_effect=Exception("error during setup")
        ):
            await tcp_connection.connect()
            mock_logger.assert_called_with("error during setup")


@pytest.mark.asyncio
async def test_disconnect_when_already_disconnected():
    """Test that disconnecting a connection already disconnected works correctly."""
    port = get_unused_tcp_port()
    tcp_connection = _make_tcp_server_connection(
        "address", "public_key", "127.0.0.1", port
    )

    with unittest.mock.patch.object(tcp_connection.logger, "warning") as mock_logger:
        await tcp_connection.disconnect()
        mock_logger.assert_called_with("Connection already disconnected.")


@pytest.mark.asyncio
async def test_send_to_unknown_destination():
    """Test that a message to an unknown destination logs an error."""
    address = "address"
    port = get_unused_tcp_port()
    tcp_connection = _make_tcp_server_connection(
        "address", "public_key", "127.0.0.1", port
    )
    envelope = Envelope(
        to="non_existing_destination",
        sender="address",
        protocol_specification_id=DefaultMessage.protocol_specification_id,
        message=b"",
    )
    with unittest.mock.patch.object(tcp_connection.logger, "error") as mock_logger:
        await tcp_connection.send(envelope)
        mock_logger.assert_called_with(
            "[{}]: Cannot send envelope {}".format(address, envelope)
        )


@pytest.mark.asyncio
async def test_send_cancelled():
    """Test that cancelling a send works correctly."""
    port = get_unused_tcp_port()
    tcp_server = _make_tcp_server_connection(
        "address_server", "public_key", "127.0.0.1", port
    )
    tcp_client = _make_tcp_client_connection(
        "address_client", "public_key_client", "127.0.0.1", port
    )

    await tcp_server.connect()
    await tcp_client.connect()

    with unittest.mock.patch.object(
        tcp_client._writer, "drain", side_effect=CancelledError
    ):
        envelope = Envelope(
            to="address_client",
            sender="address_server",
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=b"",
        )
        await tcp_client.send(envelope)

    await tcp_client.disconnect()
    await tcp_server.disconnect()

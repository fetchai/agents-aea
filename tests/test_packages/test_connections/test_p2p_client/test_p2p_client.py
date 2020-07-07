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

"""Peer to Peer connection and channel."""

import asyncio
import logging
from unittest import mock
from unittest.mock import MagicMock

import fetch.p2p.api.http_calls

from fetchai.ledger.crypto import entity

import pytest

from aea.mail.base import Envelope

from tests.conftest import (
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    _make_p2p_client_connection,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestP2p:
    """Contains the test for the p2p connection."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = "127.0.0.1"
        cls.port = 8000
        m_fet_key = "6d56fd47e98465824aa85dfe620ad3dbf092b772abc6c6a182e458b5c56ad13b"
        cls.ent = entity.Entity.from_hex(m_fet_key)
        cls.p2p_client_connection = _make_p2p_client_connection(
            address=cls.ent.public_key_hex,
            provider_addr=cls.address,
            provider_port=cls.port,
        )
        cls.p2p_client_connection.loop = asyncio.get_event_loop()

    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.p2p_client_connection.address == self.ent.public_key_hex

    async def test_connection(self):
        """Test the connection and disconnection from the p2p connection."""
        with mock.patch.object(
            fetch.p2p.api.http_calls.HTTPCalls, "get_messages", return_value=[]
        ):
            with mock.patch.object(
                fetch.p2p.api.http_calls.HTTPCalls,
                "register",
                return_value={"status": "OK"},
            ):
                await self.p2p_client_connection.connect()

    async def test_disconnect(self):
        """Test the connection and disconnection from the p2p connection."""
        with mock.patch.object(
            fetch.p2p.api.http_calls.HTTPCalls,
            "unregister",
            return_value={"status": "OK"},
        ):
            await self.p2p_client_connection.disconnect()
            assert self.p2p_client_connection.connection_status.is_connected is False


@pytest.mark.asyncio
async def test_p2p_receive():
    """Test receive from p2p connection."""
    address = "127.0.0.1"
    port = 8000
    m_fet_key = "6d56fd47e98465824aa85dfe620ad3dbf092b772abc6c6a182e458b5c56ad13b"
    ent = entity.Entity.from_hex(m_fet_key)
    p2p_connection = _make_p2p_client_connection(
        address=ent.public_key_hex, provider_addr=address, provider_port=port,
    )
    p2p_connection.loop = asyncio.get_event_loop()

    fake_get_messages_empty = MagicMock(return_value=[])

    s_msg = {
        "FROM": {"NODE_ADDRESS": "node_address", "SENDER_ADDRESS": "sender_address"},
        "TO": {"NODE_ADDRESS": "node_address", "RECEIVER_ADDRESS": "receiver_address"},
        "PROTOCOL": "author/protocol_name:0.1.0",
        "CONTEXT": "context",
        "PAYLOAD": "payload",
    }
    messages = [s_msg]

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "get_messages", return_value=[]
    ):
        with mock.patch.object(
            fetch.p2p.api.http_calls.HTTPCalls,
            "register",
            return_value={"status": "OK"},
        ):
            await p2p_connection.connect()
            assert p2p_connection.connection_status.is_connected is True

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "get_messages", return_value=messages
    ) as mock_receive:
        p2p_connection.channel._httpCall.get_messages = mock_receive
        await asyncio.sleep(2.0)
        envelope = await p2p_connection.receive()
        assert envelope is not None

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "unregister", return_value={"status": "OK"}
    ):
        p2p_connection.channel._httpCall.get_messages = fake_get_messages_empty
        await p2p_connection.disconnect()
        assert p2p_connection.connection_status.is_connected is False


@pytest.mark.asyncio
async def test_p2p_send():
    """Test the send functionality of the p2p connection."""
    address = "127.0.0.1"
    port = 8000
    m_fet_key = "6d56fd47e98465824aa85dfe620ad3dbf092b772abc6c6a182e458b5c56ad13b"
    ent = entity.Entity.from_hex(m_fet_key)
    p2p_client_connection = _make_p2p_client_connection(
        address=ent.public_key_hex, provider_addr=address, provider_port=port,
    )
    p2p_client_connection.loop = asyncio.get_event_loop()
    envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=b"Hello",
    )

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "get_messages", return_value=[]
    ):
        with mock.patch.object(
            fetch.p2p.api.http_calls.HTTPCalls,
            "register",
            return_value={"status": "OK"},
        ):
            await p2p_client_connection.connect()
            assert p2p_client_connection.connection_status.is_connected is True

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "get_messages", return_value=[]
    ):
        with mock.patch.object(
            fetch.p2p.api.http_calls.HTTPCalls,
            "send_message",
            return_value={"status": "OK"},
        ):
            await p2p_client_connection.send(envelope=envelope)
            # TODO: Consider returning the response from the server in order to be able to assert that the message send!
            assert True

    with mock.patch.object(
        fetch.p2p.api.http_calls.HTTPCalls, "unregister", return_value={"status": "OK"},
    ):
        await p2p_client_connection.disconnect()
        assert p2p_client_connection.connection_status.is_connected is False

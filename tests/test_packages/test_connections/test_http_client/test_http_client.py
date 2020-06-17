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
"""Tests for the HTTP Client connection and channel."""
import asyncio
import logging
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.protocols.http.message import HttpMessage

from ....conftest import (
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestHTTPClientConnect:
    """Tests the http client connection's 'connect' functionality."""

    def setup(self):
        """Initialise the class."""
        self.address = get_host()
        self.port = get_unused_tcp_port()
        self.agent_identity = Identity("name", address="some string")
        configuration = ConnectionConfig(
            host=self.address,
            port=self.port,
            connection_id=HTTPClientConnection.connection_id,
        )
        self.http_client_connection = HTTPClientConnection(
            configuration=configuration, identity=self.agent_identity
        )
        self.http_client_connection.loop = asyncio.get_event_loop()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.http_client_connection.address == self.agent_identity.address

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test the connect functionality of the http client connection."""
        await self.http_client_connection.connect()
        assert self.http_client_connection.connection_status.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test the disconnect functionality of the http client connection."""
        await self.http_client_connection.connect()
        assert self.http_client_connection.connection_status.is_connected is True

        await self.http_client_connection.disconnect()
        assert self.http_client_connection.connection_status.is_connected is False

    @pytest.mark.asyncio
    async def test_http_send_error(self):
        """Test request fails and send back result with code 600."""
        await self.http_client_connection.connect()

        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="bad url",
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=request_http_message,
        )

        connection_response_mock = Mock()
        connection_response_mock.status_code = 200

        await self.http_client_connection.send(envelope=request_envelope)
        # TODO: Consider returning the response from the server in order to be able to assert that the message send!
        envelope = await asyncio.wait_for(
            self.http_client_connection.receive(), timeout=10
        )
        assert envelope
        assert envelope.message.status_code == 600

        await self.http_client_connection.disconnect()

    @pytest.mark.asyncio
    async def test_http_send_ok(self):
        """Test request is ok cause mocked."""
        await self.http_client_connection.connect()

        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="https://not-a-google.com",
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=request_http_message,
        )

        connection_response_mock = Mock()
        connection_response_mock.status_code = 200

        response_mock = Mock()
        response_mock.status = 200
        response_mock.headers = {"headers": "some header"}
        response_mock.reason = "OK"
        response_mock._body = b"Some content"

        async def request_coro(*args, **kwargs):
            return response_mock

        with patch.object(
            self.http_client_connection.channel,
            "_perform_http_request",
            new=Mock(wraps=request_coro),
        ):
            await self.http_client_connection.send(envelope=request_envelope)
            # TODO: Consider returning the response from the server in order to be able to assert that the message send!
            envelope = await asyncio.wait_for(
                self.http_client_connection.receive(), timeout=10
            )

        assert envelope
        assert (
            envelope.message.status_code == response_mock.status
        ), envelope.message.bodyy.decode("utf-8")

        await self.http_client_connection.disconnect()

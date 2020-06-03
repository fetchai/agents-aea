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
from unittest import mock
from unittest.mock import Mock

import pytest

import requests

from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

from ....conftest import (
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestHTTPClientConnect:
    """Tests the http client connection's 'connect' functionality."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = get_host()
        cls.port = get_unused_tcp_port()
        cls.agent_identity = Identity("name", address="some string")
        configuration = ConnectionConfig(
            address=cls.address,
            port=cls.port,
            connection_id=HTTPClientConnection.connection_id,
        )
        cls.http_client_connection = HTTPClientConnection(
            configuration=configuration, identity=cls.agent_identity
        )
        cls.http_client_connection.loop = asyncio.get_event_loop()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.http_client_connection.address == self.agent_identity.address

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test the connect functionality of the http client connection."""
        connection_response_mock = Mock()
        connection_response_mock.status_code = 200

        with mock.patch.object(
            requests, "request", return_value=connection_response_mock
        ):
            await self.http_client_connection.connect()
            assert self.http_client_connection.connection_status.is_connected is True


@pytest.mark.asyncio
class TestHTTPClientDisconnection:
    """Tests the http client connection's 'disconnect' functionality."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = get_host()
        cls.port = get_unused_tcp_port()
        cls.agent_identity = Identity("name", address="some string")
        configuration = ConnectionConfig(
            address=cls.address,
            port=cls.port,
            connection_id=HTTPClientConnection.connection_id,
        )
        cls.http_client_connection = HTTPClientConnection(
            configuration=configuration, identity=cls.agent_identity,
        )
        cls.http_client_connection.loop = asyncio.get_event_loop()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test the disconnect functionality of the http client connection."""
        connection_response_mock = Mock()
        connection_response_mock.status_code = 200

        with mock.patch.object(
            requests, "request", return_value=connection_response_mock
        ):
            await self.http_client_connection.connect()
            assert self.http_client_connection.connection_status.is_connected is True

        await self.http_client_connection.disconnect()
        assert self.http_client_connection.connection_status.is_connected is False


@pytest.mark.asyncio
async def test_http_send():
    """Test the send functionality of the http client connection."""
    address = get_host()
    port = get_unused_tcp_port()
    agent_identity = Identity("name", address="some agent address")

    configuration = ConnectionConfig(
        address=address, port=port, connection_id=HTTPClientConnection.connection_id
    )
    http_client_connection = HTTPClientConnection(
        configuration=configuration, identity=agent_identity
    )
    http_client_connection.loop = asyncio.get_event_loop()

    request_http_message = HttpMessage(
        dialogue_reference=("", ""),
        target=0,
        message_id=1,
        performative=HttpMessage.Performative.REQUEST,
        method="",
        url="",
        headers="",
        version="",
        bodyy=b"",
    )
    request_envelope = Envelope(
        to="receiver",
        sender="sender",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=HttpSerializer().encode(request_http_message),
    )

    connection_response_mock = Mock()
    connection_response_mock.status_code = 200

    with mock.patch.object(requests, "request", return_value=connection_response_mock):
        await http_client_connection.connect()
        assert http_client_connection.connection_status.is_connected is True

    send_response_mock = Mock()
    send_response_mock.status_code = 200
    send_response_mock.headers = {"headers": "some header"}
    send_response_mock.reason = "OK"
    send_response_mock.content = b"Some content"

    with mock.patch.object(requests, "request", return_value=send_response_mock):
        await http_client_connection.send(envelope=request_envelope)
        # TODO: Consider returning the response from the server in order to be able to assert that the message send!
        assert True

    await http_client_connection.disconnect()
    assert http_client_connection.connection_status.is_connected is False

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

"""Tests for the webhook connection and channel."""

import asyncio
import logging
from unittest import mock
from unittest.mock import Mock

import pytest

import requests

from aea.mail.base import Envelope

# from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.connections.webhook.connection import WebhookConnection
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

from ....conftest import (
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestWebhookConnect:
    """Tests the webhook connection's 'connect' functionality."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = get_host()
        cls.port = get_unused_tcp_port()
        cls.agent_address = "some string"

        cls.webhook_connection = WebhookConnection(
            address=cls.agent_address,
            webhook_address=cls.address,
            webhook_port=cls.port,
            webhook_url_path="/webhooks/topic/{topic}/",
        )
        cls.webhook_connection.loop = asyncio.get_event_loop()

    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.webhook_connection.address == self.agent_address

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True

@pytest.mark.asyncio
class TestWebhookDisconnection:
    """Tests the webhook connection's 'disconnect' functionality."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.address = get_host()
        cls.port = get_unused_tcp_port()
        cls.agent_address = "some string"

        cls.webhook_connection = WebhookConnection(
            address=cls.agent_address,
            webhook_address=cls.address,
            webhook_port=cls.port,
            webhook_url_path="/webhooks/topic/{topic}/",
        )
        cls.webhook_connection.loop = asyncio.get_event_loop()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test the disconnect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True

        await self.webhook_connection.disconnect()
        assert self.webhook_connection.connection_status.is_connected is False


@pytest.mark.asyncio
async def test_webhook_receive():
    """Test the receive functionality of the webhook connection."""
    address = "127.0.0.1"
    port = 8050
    agent_address = "some agent address"

    webhook_connection = WebhookConnection(
        address=agent_address,
        webhook_address=address,
        webhook_port=port,
        webhook_url_path="/webhooks/topic/{topic}/",
    )
    webhook_connection.loop = asyncio.get_event_loop()

    # create a dummy server to send webhook notifications
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

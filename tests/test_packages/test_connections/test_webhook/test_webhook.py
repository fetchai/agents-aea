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
import json
import logging
from traceback import print_exc
from typing import cast

import aiohttp
from aiohttp.client_reqrep import ClientResponse

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.identity.base import Identity
from aea.mail.base import Envelope


from packages.fetchai.connections.webhook.connection import WebhookConnection
from packages.fetchai.protocols.http.message import HttpMessage

from tests.conftest import (
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestWebhookConnection:
    """Tests the webhook connection's 'connect' functionality."""

    def setup(self):
        """Initialise the class."""
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.identity = Identity("", address="some string")
        self.path = "/webhooks/topic/{topic}/"
        self.loop = asyncio.get_event_loop()

        configuration = ConnectionConfig(
            webhook_address=self.host,
            webhook_port=self.port,
            webhook_url_path=self.path,
            connection_id=WebhookConnection.connection_id,
        )
        self.webhook_connection = WebhookConnection(
            configuration=configuration, identity=self.identity,
        )
        self.webhook_connection.loop = self.loop

    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.webhook_connection.address == self.identity.address

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test the disconnect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True

        await self.webhook_connection.disconnect()
        assert self.webhook_connection.connection_status.is_connected is False

    def teardown(self):
        """Close connection after testing."""
        try:
            self.loop.run_until_complete(self.webhook_connection.disconnect())
        except Exception:
            print_exc()
            raise

    @pytest.mark.asyncio
    async def test_receive_post_ok(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True
        payload = {"hello": "world"}
        call_task = self.loop.create_task(self.call_webhook("test_topic", json=payload))
        envelope = await asyncio.wait_for(self.webhook_connection.receive(), timeout=10)

        assert envelope

        message = cast(HttpMessage, envelope.message)
        assert message.method.upper() == "POST"
        assert message.bodyy.decode("utf-8") == json.dumps(payload)
        await call_task

    @pytest.mark.asyncio
    async def test_send(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.connection_status.is_connected is True

        http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="/",
            headers="",
            bodyy="",
            version="",
        )
        envelope = Envelope(
            to="addr",
            sender="my_id",
            protocol_id=PublicId.from_str("fetchai/http:0.3.0"),
            message=http_message,
        )
        await self.webhook_connection.send(envelope)

    async def call_webhook(self, topic: str, **kwargs) -> ClientResponse:
        """
        Make a http request to a webhook.

        :param topic: topic to use
        :params **kwargs: data or json for payload

        :return: http response
        """
        path = self.path.format(topic=topic)
        method = kwargs.get("method", "post")
        url = f"http://{self.host}:{self.port}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as resp:
                    await resp.read()
                    return resp
        except Exception:
            print_exc()
            raise

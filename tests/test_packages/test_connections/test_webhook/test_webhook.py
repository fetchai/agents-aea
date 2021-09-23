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
from unittest.mock import MagicMock, patch

import aiohttp
import pytest
from aiohttp.client_reqrep import ClientResponse

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue

from packages.fetchai.connections.webhook.connection import WebhookConnection
from packages.fetchai.protocols.http.dialogues import HttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage

from tests.common.mocks import RegexComparator
from tests.conftest import get_host, get_unused_tcp_port


logger = logging.getLogger(__name__)


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.CLIENT

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.asyncio
class TestWebhookConnection:
    """Tests the webhook connection's 'connect' functionality."""

    def setup(self):
        """Initialise the class."""
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.target_skill_id = "some_author/some_skill:0.1.0"
        self.identity = Identity(
            "identity", address="some string", public_key="some public_key"
        )
        self.path = "/webhooks/topic/{topic}/"
        self.loop = asyncio.get_event_loop()

        configuration = ConnectionConfig(
            webhook_address=self.host,
            webhook_port=self.port,
            webhook_url_path=self.path,
            target_skill_id=self.target_skill_id,
            connection_id=WebhookConnection.connection_id,
        )
        self.webhook_connection = WebhookConnection(
            configuration=configuration, data_dir=MagicMock(), identity=self.identity,
        )
        self.skill_dialogues = HttpDialogues(self.target_skill_id)

    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.webhook_connection.address == self.identity.address

    @pytest.mark.asyncio
    async def test_connection(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test the disconnect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.is_connected is True

        await self.webhook_connection.disconnect()
        assert self.webhook_connection.is_connected is False

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
        assert self.webhook_connection.is_connected is True
        payload = {"hello": "world"}
        call_task = self.loop.create_task(self.call_webhook("test_topic", json=payload))
        envelope = await asyncio.wait_for(self.webhook_connection.receive(), timeout=10)

        assert envelope

        message = cast(HttpMessage, envelope.message)
        dialogue = self.skill_dialogues.update(message)
        assert dialogue is not None
        assert message.method.upper() == "POST"
        assert message.body.decode("utf-8") == json.dumps(payload)
        await call_task

    @pytest.mark.asyncio
    async def test_send(self):
        """Test the connect functionality of the webhook connection."""
        await self.webhook_connection.connect()
        assert self.webhook_connection.is_connected is True

        http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="/",
            headers="",
            body="",
            version="",
        )
        envelope = Envelope(to="addr", sender="my_id", message=http_message,)
        with patch.object(self.webhook_connection.logger, "warning") as mock_logger:
            await self.webhook_connection.send(envelope)
            await asyncio.sleep(0.01)
            mock_logger.assert_any_call(
                RegexComparator(
                    "Dropping envelope=.* as sending via the webhook is not possible!"
                )
            )

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

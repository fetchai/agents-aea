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
import subprocess  # nosec
import time

# from unittest import mock
# from unittest.mock import Mock
#
# from aiohttp import web  # type: ignore
#
# from multidict import CIMultiDict, CIMultiDictProxy  # type: ignore

import pytest

# from yarl import URL  # type: ignore
from aea.identity.base import Identity
from packages.fetchai.connections.webhook.connection import WebhookConnection

from ....conftest import (
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
        cls.identity = Identity("", address="some string")

        cls.webhook_connection = WebhookConnection(
            identity=cls.identity,
            webhook_address=cls.address,
            webhook_port=cls.port,
            webhook_url_path="/webhooks/topic/{topic}/",
        )
        cls.webhook_connection.loop = asyncio.get_event_loop()

    async def test_initialization(self):
        """Test the initialisation of the class."""
        assert self.webhook_connection.address == self.identity.address

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
        cls.identity = Identity("", address="some string")

        cls.webhook_connection = WebhookConnection(
            identity=cls.identity,
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


# ToDo: testing webhooks received
# @pytest.mark.asyncio
# async def test_webhook_receive():
#     """Test the receive functionality of the webhook connection."""
#     admin_address = "127.0.0.1"
#     admin_port = 8051
#     webhook_address = "127.0.0.1"
#     webhook_port = 8052
#     agent_address = "some agent address"
#
#     webhook_connection = WebhookConnection(
#         address=agent_address,
#         webhook_address=webhook_address,
#         webhook_port=webhook_port,
#         webhook_url_path="/webhooks/topic/{topic}/",
#     )
#     webhook_connection.loop = asyncio.get_event_loop()
#     await webhook_connection.connect()
#
#
#
#     # # Start an aries agent process
#     # process = start_aca(admin_address, admin_port)
#
#     received_webhook_envelop = await webhook_connection.receive()
#     logger.info(received_webhook_envelop)

#     webhook_request_mock = Mock()
#     webhook_request_mock.method = "POST"
#     webhook_request_mock.url = URL(val="some url")
#     webhook_request_mock.version = (1, 1)
#     webhook_request_mock.headers = CIMultiDictProxy(CIMultiDict(a="Ali"))
#     webhook_request_mock.body = b"some body"
#
#     with mock.patch.object(web.Request, "__init__", return_value=webhook_request_mock):
#         received_webhook_envelop = await webhook_connection.receive()
#         logger.info(received_webhook_envelop)
#
#     # process.terminate()


def start_aca(admin_address: str, admin_port: int):
    process = subprocess.Popen(  # nosec
        [
            "aca-py",
            "start",
            "--admin",
            admin_address,
            str(admin_port),
            "--admin-insecure-mode",
            "--inbound-transport",
            "http",
            "0.0.0.0",
            "8000",
            "--outbound-transport",
            "http",
            "--webhook-url",
            "http://127.0.0.1:8052/webhooks",
        ]
    )
    time.sleep(4.0)
    return process

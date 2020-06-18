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
"""This module contains the tests of the HTTP Server connection module."""
import asyncio
import logging
import os
from traceback import print_exc
from typing import cast

import aiohttp
from aiohttp.client_reqrep import ClientResponse

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.http_server.connection import HTTPServerConnection
from packages.fetchai.protocols.http.message import HttpMessage

from ....conftest import (
    ROOT_DIR,
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestHTTPServer:
    """Tests for HTTPServer connection."""

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """
        Make a http request.

        :param method: HTTP method: GET, POST etc
        :param path: path to request on server. full url constructed automatically

        :return: http response
        """
        try:
            url = f"http://{self.host}:{self.port}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as resp:
                    await resp.read()
                    return resp
        except Exception:
            print_exc()
            raise

    def setup(self):
        """Initialise the test case."""
        self.identity = Identity("name", address="my_key")
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.api_spec_path = os.path.join(
            ROOT_DIR, "tests", "data", "petstore_sim.yaml"
        )
        self.connection_id = HTTPServerConnection.connection_id
        self.protocol_id = PublicId.from_str("fetchai/http:0.2.0")

        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            api_spec_path=self.api_spec_path,
            connection_id=HTTPServerConnection.connection_id,
            restricted_to_protocols=set([self.protocol_id]),
        )
        self.http_connection = HTTPServerConnection(
            configuration=self.configuration, identity=self.identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.http_connection.connect())

    @pytest.mark.asyncio
    async def test_http_connection_disconnect_channel(self):
        """Test the disconnect."""
        await self.http_connection.channel.disconnect()
        assert self.http_connection.channel.is_stopped

    @pytest.mark.asyncio
    async def test_get_200(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message = cast(HttpMessage, envelope.message)
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=incoming_message.message_id,
            message_id=incoming_message.message_id + 1,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=200,
            status_text="Success",
            bodyy=b"Response body",
        )
        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            protocol_id=envelope.protocol_id,
            context=envelope.context,
            message=message,
        )
        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(request_task, timeout=20,)

        assert (
            response.status == 200
            and response.reason == "Success"
            and await response.text() == "Response body"
        )

    @pytest.mark.asyncio
    async def test_post_201(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(self.request("post", "/pets",))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message = cast(HttpMessage, envelope.message)
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=incoming_message.message_id,
            message_id=incoming_message.message_id + 1,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=201,
            status_text="Created",
            bodyy=b"Response body",
        )
        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            protocol_id=envelope.protocol_id,
            context=envelope.context,
            message=message,
        )
        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(request_task, timeout=20,)
        assert (
            response.status == 201
            and response.reason == "Created"
            and await response.text() == "Response body"
        )

    @pytest.mark.asyncio
    async def test_get_404(self):
        """Test send post request w/ 404 response."""
        response = await self.request("get", "/url-non-exists")

        assert (
            response.status == 404
            and response.reason == "Request Not Found"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_post_404(self):
        """Test send post request w/ 404 response."""
        response = await self.request("get", "/url-non-exists", data="some data")

        assert (
            response.status == 404
            and response.reason == "Request Not Found"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_get_408(self):
        """Test send post request w/ 404 response."""
        await self.http_connection.connect()
        self.http_connection.channel.RESPONSE_TIMEOUT = 0.1
        response = await self.request("get", "/pets")

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_post_408(self):
        """Test send post request w/ 404 response."""
        self.http_connection.channel.RESPONSE_TIMEOUT = 0.1
        response = await self.request("post", "/pets", data="somedata")

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_send_connection_drop(self):
        """Test unexpected response."""
        client_id = "to_key"
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=1,
            message_id=2,
            headers="",
            version="",
            status_code=200,
            status_text="Success",
            bodyy=b"",
        )
        envelope = Envelope(
            to=client_id,
            sender="from_key",
            protocol_id=self.protocol_id,
            message=message,
        )
        await self.http_connection.send(envelope)

    def teardown(self):
        """Teardown the test case."""
        self.loop.run_until_complete(self.http_connection.disconnect())

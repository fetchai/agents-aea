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
from unittest.mock import Mock, patch

import aiohttp
from aiohttp.client_reqrep import ClientResponse

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.http_server.connection import (
    APISpec,
    HTTPServerConnection,
    Response,
)
from packages.fetchai.protocols.http.message import HttpMessage

from tests.conftest import (
    HTTP_PROTOCOL_PUBLIC_ID,
    ROOT_DIR,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
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
        self.protocol_id = PublicId.from_str("fetchai/http:0.3.0")

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
    async def test_bad_performative_get_server_error(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message = cast(HttpMessage, envelope.message)
        message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
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

        assert response.status == 500 and await response.text() == "Server error"

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

    @pytest.mark.asyncio
    async def test_get_message_channel_not_connected(self):
        """Test error on channel get message if not connected."""
        await self.http_connection.disconnect()
        with pytest.raises(ValueError):
            await self.http_connection.channel.get_message()

    @pytest.mark.asyncio
    async def test_fail_connect(self):
        """Test error on server connection."""
        await self.http_connection.disconnect()

        with patch.object(
            self.http_connection.channel,
            "_start_http_server",
            side_effect=Exception("expected"),
        ):
            await self.http_connection.connect()
        assert not self.http_connection.connection_status.is_connected

    @pytest.mark.asyncio
    async def test_server_error_on_send_response(self):
        """Test exception raised on response sending to the client."""
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

        with patch.object(Response, "from_envelope", side_effect=Exception("expected")):
            await self.http_connection.send(response_envelope)
            response = await asyncio.wait_for(request_task, timeout=20,)

        assert response and response.status == 500 and response.reason == "Server Error"

    @pytest.mark.asyncio
    async def test_send_envelope_restricted_to_protocols_fail(self):
        """Test fail on send if envelope protocol not supported."""
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=1,
            message_id=2,
            version="1.0",
            headers="",
            status_code=200,
            status_text="Success",
            bodyy=b"Response body",
        )
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message,
        )

        with patch.object(
            self.http_connection.channel,
            "restricted_to_protocols",
            new=[HTTP_PROTOCOL_PUBLIC_ID],
        ):
            with pytest.raises(ValueError):
                await self.http_connection.send(envelope)

    def teardown(self):
        """Teardown the test case."""
        self.loop.run_until_complete(self.http_connection.disconnect())


def test_bad_api_spec():
    """Test error on apispec file is invalid."""
    with pytest.raises(FileNotFoundError):
        APISpec("not_exist_file")


def test_apispec_verify_if_no_validator_set():
    """Test api spec ok if no spec file provided."""
    assert APISpec().verify(Mock())

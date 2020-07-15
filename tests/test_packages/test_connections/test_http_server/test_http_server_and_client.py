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
"""Tests for the HTTP Client and Server connections together."""
import asyncio
import logging
from typing import cast

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.connections.http_server.connection import HTTPServerConnection
from packages.fetchai.protocols.http.message import HttpMessage

from tests.conftest import (
    HTTP_PROTOCOL_PUBLIC_ID,
    get_host,
    get_unused_tcp_port,
)


logger = logging.getLogger(__name__)


class TestClientServer:
    """Client-Server end-to-end test."""

    def setup_server(self):
        """Set up server connection."""
        self.identity = Identity("name", address="server")
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.connection_id = HTTPServerConnection.connection_id
        self.protocol_id = PublicId.from_str("fetchai/http:0.3.0")

        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            api_spec_path=None,  # do not filter on API spec
            connection_id=HTTPServerConnection.connection_id,
            restricted_to_protocols=set([self.protocol_id]),
        )
        self.server = HTTPServerConnection(
            configuration=self.configuration, identity=self.identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.server.connect())

    def setup_client(self):
        """Set up client connection."""
        self.agent_identity = Identity("name", address="client")
        configuration = ConnectionConfig(
            host="localost",
            port="8888",  # TODO: remove host/port for client?
            connection_id=HTTPClientConnection.connection_id,
        )
        self.client = HTTPClientConnection(
            configuration=configuration, identity=self.agent_identity
        )
        self.client.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.client.connect())

    def setup(self):
        """Set up test case."""
        self.setup_server()
        self.setup_client()

    def _make_request(
        self, path: str, method: str = "get", headers: str = "", bodyy: bytes = b""
    ) -> Envelope:
        """Make request envelope."""
        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=f"http://{self.host}:{self.port}{path}",
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=request_http_message,
        )
        return request_envelope

    def _make_response(
        self, request_envelope: Envelope, status_code: int = 200, status_text: str = ""
    ) -> Envelope:
        """Make response envelope."""
        incoming_message = cast(HttpMessage, request_envelope.message)
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=incoming_message.message_id,
            message_id=incoming_message.message_id + 1,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=status_code,
            status_text=status_text,
            bodyy=incoming_message.bodyy,
        )
        response_envelope = Envelope(
            to=request_envelope.sender,
            sender=request_envelope.to,
            protocol_id=request_envelope.protocol_id,
            context=request_envelope.context,
            message=message,
        )
        return response_envelope

    @pytest.mark.asyncio
    async def test_post_with_payload(self):
        """Test client and server with post request."""
        initial_request = self._make_request("/test", "POST", bodyy=b"1234567890")
        await self.client.send(initial_request)
        request = await asyncio.wait_for(self.server.receive(), timeout=5)
        initial_response = self._make_response(request)
        await self.server.send(initial_response)
        response = await asyncio.wait_for(self.client.receive(), timeout=5)
        assert (
            cast(HttpMessage, initial_request.message).bodyy
            == cast(HttpMessage, response.message).bodyy
        )

    def teardown(self):
        """Tear down testcase."""
        self.loop.run_until_complete(self.client.disconnect())
        self.loop.run_until_complete(self.server.disconnect())

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
import email
import logging
import urllib
from typing import Dict, Optional, cast
from unittest.mock import MagicMock

import pytest

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.connections.http_server.connection import (
    HTTPServerConnection,
    headers_to_string,
)
from packages.fetchai.protocols.http.dialogues import HttpDialogue, HttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage

from tests.conftest import get_host, get_unused_tcp_port


logger = logging.getLogger(__name__)

SKILL_ID_STR = "some_author/some_skill:0.1.0"


class TestClientServer:
    """Client-Server end-to-end test."""

    def setup_server(self):
        """Set up server connection."""
        self.server_agent_address = "server_agent_address"
        self.server_agent_public_key = "server_agent_public_key"
        self.server_agent_identity = Identity(
            "agent_running_server",
            address=self.server_agent_address,
            public_key=self.server_agent_public_key,
        )
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.connection_id = HTTPServerConnection.connection_id
        self.protocol_id = HttpMessage.protocol_id
        self.target_skill_id = SKILL_ID_STR

        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            target_skill_id=self.target_skill_id,
            api_spec_path=None,  # do not filter on API spec
            connection_id=HTTPServerConnection.connection_id,
        )
        self.server = HTTPServerConnection(
            configuration=self.configuration,
            data_dir=MagicMock(),
            identity=self.server_agent_identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.server.connect())

        # skill side dialogues
        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.SERVER

        self._skill_dialogues = HttpDialogues(
            SKILL_ID_STR, role_from_first_message=role_from_first_message
        )

    def setup_client(self):
        """Set up client connection."""
        self.client_agent_address = "client_agent_address"
        self.client_agent_public_key = "client_agent_public_key"
        self.client_agent_skill_id = "some/skill:0.1.0"
        self.client_agent_identity = Identity(
            "agent_running_client",
            address=self.client_agent_address,
            public_key=self.client_agent_public_key,
        )
        configuration = ConnectionConfig(
            host="localhost",
            port="8888",  # TODO: remove host/port for client?
            connection_id=HTTPClientConnection.connection_id,
        )
        self.client = HTTPClientConnection(
            configuration=configuration,
            data_dir=MagicMock(),
            identity=self.client_agent_identity,
        )
        self.loop.run_until_complete(self.client.connect())

        # skill side dialogues
        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.CLIENT

        self._client_dialogues = HttpDialogues(
            self.client_agent_skill_id, role_from_first_message=role_from_first_message
        )

    def setup(self):
        """Set up test case."""
        self.setup_server()
        self.setup_client()

    def _make_request(
        self,
        path: str,
        method: str = "get",
        headers: Optional[Dict] = None,
        body: bytes = b"",
    ) -> Envelope:
        """Make request envelope."""
        request_http_message, _ = self._client_dialogues.create(
            counterparty=str(HTTPClientConnection.connection_id),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=f"http://{self.host}:{self.port}{path}",
            headers=headers_to_string(headers) if headers else "",
            version="",
            body=b"",
        )
        request_envelope = Envelope(
            to=request_http_message.to,
            sender=request_http_message.sender,
            message=request_http_message,
        )
        return request_envelope

    def _make_response(
        self, request_envelope: Envelope, status_code: int = 200, status_text: str = ""
    ) -> Envelope:
        """Make response envelope."""
        incoming_message = cast(HttpMessage, request_envelope.message)
        dialogue = self._skill_dialogues.update(incoming_message)
        assert dialogue is not None
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=status_code,
            status_text=status_text,
            body=incoming_message.body,
        )
        response_envelope = Envelope(
            to=message.to,
            sender=message.sender,
            context=request_envelope.context,
            message=message,
        )
        return response_envelope

    @pytest.mark.asyncio
    async def test_post_with_payload(self):
        """Test client and server with post request."""
        initial_request = self._make_request("/test", "POST", body=b"1234567890")
        await self.client.send(initial_request)
        request = await asyncio.wait_for(self.server.receive(), timeout=5)
        # this is "inside" the server agent
        initial_response = self._make_response(request)
        await self.server.send(initial_response)
        response = await asyncio.wait_for(self.client.receive(), timeout=5)
        assert (
            cast(HttpMessage, initial_request.message).body
            == cast(HttpMessage, response.message).body
        )
        assert (
            initial_request.message.dialogue_reference[0]
            == response.message.dialogue_reference[0]
        )

    @pytest.mark.asyncio
    async def test_get_with_query(self):
        """Test client and server with url query."""
        query = {"key": "value"}
        path = "/test?{}".format(urllib.parse.urlencode(query))
        initial_request = self._make_request(path, "GET")
        await self.client.send(initial_request)
        request = await asyncio.wait_for(self.server.receive(), timeout=5)
        # this is "inside" the server agent

        parsed_query = dict(
            urllib.parse.parse_qsl(
                urllib.parse.splitquery(cast(HttpMessage, request.message).url)[1]
            )
        )
        assert parsed_query == query
        initial_response = self._make_response(request)
        await self.server.send(initial_response)
        response = await asyncio.wait_for(self.client.receive(), timeout=5)

        assert (
            initial_request.message.dialogue_reference[0]
            == response.message.dialogue_reference[0]
        )

    @pytest.mark.asyncio
    async def test_headers(self):
        """Test client and server with url query."""
        headers = {"key1": "value1", "key2": "value2"}
        path = "/test"
        initial_request = self._make_request(path, "GET", headers=headers)
        await self.client.send(initial_request)

        request = await asyncio.wait_for(self.server.receive(), timeout=5)
        parsed_headers = dict(
            email.message_from_string(
                cast(HttpMessage, request.message).headers
            ).items()
        )
        assert parsed_headers.items() >= headers.items()

        initial_response = self._make_response(request)
        await self.server.send(initial_response)

        response = await asyncio.wait_for(self.client.receive(), timeout=5)
        parsed_headers = dict(
            email.message_from_string(
                cast(HttpMessage, response.message).headers
            ).items()
        )
        assert parsed_headers.items() >= headers.items()
        assert (
            initial_request.message.dialogue_reference[0]
            == response.message.dialogue_reference[0]
        )

    def teardown(self):
        """Tear down testcase."""
        self.loop.run_until_complete(self.client.disconnect())
        self.loop.run_until_complete(self.server.disconnect())

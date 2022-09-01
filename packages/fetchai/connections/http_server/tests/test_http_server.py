# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
# pylint: skip-file

import asyncio
import logging
import os
import ssl
from pathlib import Path
from traceback import print_exc
from typing import Tuple, cast
from unittest.mock import MagicMock, Mock, patch

import aiohttp
import pytest
from aiohttp.client_reqrep import ClientResponse

from aea.common import Address
from aea.configurations.base import ConnectionConfig
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.test_tools.mocks import RegexComparator
from aea.test_tools.network import get_host, get_unused_tcp_port

from packages.fetchai.connections.http_server.connection import (
    APISpec,
    HTTPServerConnection,
    Response,
)
from packages.fetchai.protocols.http.dialogues import HttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage


logger = logging.getLogger(__name__)

DATA_DIR = str(Path(__file__).parent / "data")


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :param self_address: self address
        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.asyncio
class TestHTTPServer:
    """Tests for HTTPServer connection."""

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """
        Make a http request.

        :param method: HTTP method: GET, POST etc
        :param path: path to request on server. full url constructed automatically
        :param kwargs: keyword arguments
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
        self.identity = Identity("name", address="my_key", public_key="my_public_key")
        self.agent_address = self.identity.address
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.api_spec_path = os.path.join(DATA_DIR, "petstore_sim.yaml")
        self.connection_id = HTTPServerConnection.connection_id
        self.protocol_id = HttpMessage.protocol_id
        self.target_skill_id = "some_author/some_skill:0.1.0"

        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            target_skill_id=self.target_skill_id,
            api_spec_path=self.api_spec_path,
            connection_id=HTTPServerConnection.connection_id,
            restricted_to_protocols={HttpMessage.protocol_id},
        )
        self.http_connection = HTTPServerConnection(
            configuration=self.configuration,
            data_dir=MagicMock(),
            identity=self.identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.http_connection.connect())
        self.connection_address = str(HTTPServerConnection.connection_id)
        self._dialogues = HttpDialogues(self.target_skill_id)
        self.original_timeout = self.http_connection.channel.timeout_window

    @pytest.mark.asyncio
    async def test_http_connection_disconnect_channel(self):
        """Test the disconnect."""
        await self.http_connection.channel.disconnect()
        assert self.http_connection.channel.is_stopped

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[HttpMessage, HttpDialogue]:
        message = cast(HttpMessage, envelope.message)
        dialogue = cast(HttpDialogue, self._dialogues.update(message))
        assert dialogue is not None
        return message, dialogue

    @pytest.mark.asyncio
    async def test_get_200(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            status_code=200,
            status_text="Success",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )
        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(
            request_task,
            timeout=20,
        )

        assert (
            response.status == 200
            and response.reason == "Success"
            and await response.text() == "Response body"
        )

    @pytest.mark.asyncio
    async def test_header_content_type(self):
        """Test send get request w/ 200 response."""
        content_type = "something/unique"
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            headers=f"Content-Type: {content_type}",
            status_code=200,
            status_text="Success",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )
        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(
            request_task,
            timeout=20,
        )
        assert (
            response.status == 200
            and response.reason == "Success"
            and await response.text() == "Response body"
        )
        assert response.headers["Content-Type"] == content_type

    @pytest.mark.asyncio
    async def test_bad_performative_get_timeout_error(self):
        """Test send get request w/ 200 response."""
        self.http_connection.channel.timeout_window = 3
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=10)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        incorrect_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            target=incoming_message.message_id,
            message_id=incoming_message.message_id + 1,
            method="post",
            url="/pets",
            version=incoming_message.version,
            headers=incoming_message.headers,
            body=b"Request body",
        )
        incorrect_message.to = incoming_message.sender

        # the incorrect message cannot be sent into a dialogue, so this is omitted.

        response_envelope = Envelope(
            to=incorrect_message.to,
            sender=envelope.to,
            context=envelope.context,
            message=incorrect_message,
        )
        with patch.object(self.http_connection.logger, "warning") as mock_logger:
            await self.http_connection.send(response_envelope)
            mock_logger.assert_any_call(
                f"Could not create dialogue for message={incorrect_message}"
            )

        response = await asyncio.wait_for(request_task, timeout=10)

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_late_message_get_timeout_error(self):
        """Test send get request w/ 200 response."""
        self.http_connection.channel.timeout_window = 1
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=10)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=200,
            status_text="Success",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=message.to,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )
        await asyncio.sleep(1.5)
        with patch.object(self.http_connection.logger, "warning") as mock_logger:
            await self.http_connection.send(response_envelope)
            mock_logger.assert_any_call(
                RegexComparator(
                    "Dropping message=.* for incomplete_dialogue_label=.* which has timed out."
                )
            )

        response = await asyncio.wait_for(request_task, timeout=10)

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_post_201(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(
            self.request(
                "post",
                "/pets",
            )
        )
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            status_code=201,
            status_text="Created",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=message.to,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )

        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(
            request_task,
            timeout=20,
        )
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
        self.http_connection.channel.timeout_window = 0.1
        with patch.object(
            self.http_connection.channel.logger, "warning"
        ) as mock_logger:
            response = await self.request("get", "/pets")
            mock_logger.assert_any_call(
                RegexComparator("Request timed out! Request=.*")
            )

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_post_408(self):
        """Test send post request w/ 404 response."""
        self.http_connection.channel.timeout_window = 0.1
        response = await self.request("post", "/pets", data="somedata")

        assert (
            response.status == 408
            and response.reason == "Request Timeout"
            and await response.text() == ""
        )

    @pytest.mark.asyncio
    async def test_send_connection_drop(self):
        """Test unexpected response."""
        message = HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,
            dialogue_reference=("", ""),
            target=1,
            message_id=2,
            headers="",
            version="",
            status_code=200,
            status_text="Success",
            body=b"",
        )
        message.to = str(HTTPServerConnection.connection_id)
        message.sender = self.target_skill_id
        envelope = Envelope(
            to=message.to,
            sender=message.sender,
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
        assert not self.http_connection.is_connected

    @pytest.mark.asyncio
    async def test_server_error_on_send_response(self):
        """Test exception raised on response sending to the client."""
        request_task = self.loop.create_task(
            self.request(
                "post",
                "/pets",
            )
        )
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            headers=incoming_message.headers,
            status_code=201,
            status_text="Created",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=message.to,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )

        with patch.object(Response, "from_message", side_effect=Exception("expected")):
            await self.http_connection.send(response_envelope)
            response = await asyncio.wait_for(
                request_task,
                timeout=20,
            )

        assert response and response.status == 500 and response.reason == "Server Error"

    def teardown(self):
        """Teardown the test case."""
        self.loop.run_until_complete(self.http_connection.disconnect())
        self.http_connection.channel.timeout_window = self.original_timeout


def test_bad_api_spec():
    """Test error on apispec file is invalid."""
    with pytest.raises(FileNotFoundError):
        APISpec("not_exist_file")


def test_apispec_verify_if_no_validator_set():
    """Test api spec ok if no spec file provided."""
    assert APISpec().verify(Mock())


@pytest.mark.asyncio
class TestHTTPSServer:
    """Tests for HTTPServer connection."""

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """
        Make a http request.

        :param method: HTTP method: GET, POST etc
        :param path: path to request on server. full url constructed automatically
        :param kwargs: keyword arguments
        :return: http response
        """
        try:
            url = f"https://{self.host}:{self.port}{path}"
            sslcontext = ssl.create_default_context(cafile=self.ssl_cert)
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, **kwargs, ssl=sslcontext
                ) as resp:
                    await resp.read()
                    return resp
        except Exception:
            print_exc()
            raise

    def setup(self):
        """Initialise the test case."""
        self.identity = Identity("name", address="my_key", public_key="my_public_key")
        self.agent_address = self.identity.address
        self.host = "localhost"
        self.port = get_unused_tcp_port()
        self.api_spec_path = os.path.join(DATA_DIR, "petstore_sim.yaml")
        self.connection_id = HTTPServerConnection.connection_id
        self.protocol_id = HttpMessage.protocol_id
        self.target_skill_id = "some_author/some_skill:0.1.0"
        self.ssl_cert = os.path.join(DATA_DIR, "certs", "server.crt")
        self.ssl_key = os.path.join(DATA_DIR, "certs", "server.key")
        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            target_skill_id=self.target_skill_id,
            api_spec_path=self.api_spec_path,
            connection_id=HTTPServerConnection.connection_id,
            restricted_to_protocols={HttpMessage.protocol_id},
            ssl_cert=self.ssl_cert,
            ssl_key=self.ssl_key,
        )
        self.http_connection = HTTPServerConnection(
            configuration=self.configuration,
            data_dir=MagicMock(),
            identity=self.identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.http_connection.connect())
        self.connection_address = str(HTTPServerConnection.connection_id)
        self._dialogues = HttpDialogues(self.target_skill_id)
        self.original_timeout = self.http_connection.channel.timeout_window

    @pytest.mark.asyncio
    async def test_get_200(self):
        """Test send get request w/ 200 response."""
        request_task = self.loop.create_task(self.request("get", "/pets"))
        envelope = await asyncio.wait_for(self.http_connection.receive(), timeout=20)
        assert envelope
        incoming_message, dialogue = self._get_message_and_dialogue(envelope)
        message = dialogue.reply(
            target_message=incoming_message,
            performative=HttpMessage.Performative.RESPONSE,
            version=incoming_message.version,
            status_code=200,
            status_text="Success",
            body=b"Response body",
        )
        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            context=envelope.context,
            message=message,
        )
        await self.http_connection.send(response_envelope)

        response = await asyncio.wait_for(
            request_task,
            timeout=20,
        )

        assert (
            response.status == 200
            and response.reason == "Success"
            and await response.text() == "Response body"
        )

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[HttpMessage, HttpDialogue]:
        message = cast(HttpMessage, envelope.message)
        dialogue = cast(HttpDialogue, self._dialogues.update(message))
        assert dialogue is not None
        return message, dialogue

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
import concurrent.futures
import functools
import http.client
import logging
import os
from threading import Thread
from typing import Dict, Tuple, cast

import pytest

from aea.configurations.base import PublicId
from aea.mail.base import Envelope

from packages.fetchai.connections.http_server.connection import HTTPServerConnection
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

from ....conftest import (
    ROOT_DIR,
    get_host,
    get_unused_tcp_port,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestHTTPServerConnectionConnectDisconnect:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class and test connect."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        assert cls.http_connection.channel.is_stopped

        cls.http_connection.channel.connect()
        assert not cls.http_connection.channel.is_stopped

    @pytest.mark.asyncio
    async def test_http_connection_disconnect_channel(self):
        """Test the disconnect."""
        self.http_connection.channel.disconnect()
        assert self.http_connection.channel.is_stopped


@pytest.mark.asyncio
class TestHTTPServerConnectionSend:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        loop = asyncio.get_event_loop()
        value = loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected

    @pytest.mark.asyncio
    async def test_send_connection_drop(self):
        """Test send connection error."""
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
            message=HttpSerializer().encode(message),
        )
        await self.http_connection.send(envelope)
        # we expect the envelope to be dropped
        assert (
            self.http_connection.channel.dispatch_ready_envelopes.get(client_id) is None
        )

    @pytest.mark.asyncio
    async def test_send_connection_send(self):
        """Test send connection error."""
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
            message=HttpSerializer().encode(message),
        )
        self.http_connection.channel.pending_request_ids.add("to_key")
        await self.http_connection.send(envelope)
        assert (
            self.http_connection.channel.dispatch_ready_envelopes.get(client_id)
            == envelope
        )
        assert self.http_connection.channel.pending_request_ids == set()
        # clean up:
        self.http_connection.channel.dispatch_ready_envelopes = (
            {}
        )  # type: Dict[str, Envelope]

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        loop = asyncio.get_event_loop()
        value = loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionGET404:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        # cls.loop.set_debug(enabled=True)
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_get_404(self):
        """Test send post request w/ 404 response."""

        def request_response_cycle(host, port) -> Tuple[int, str, bytes]:
            conn = http.client.HTTPConnection(host, port)
            conn.request("GET", "/")
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port) -> Tuple[int, str, bytes]:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        response_status_code, response_status_text, response_body = await client_thread(
            self.host, self.port
        )

        assert (
            response_status_code == 404
            and response_status_text == "Request Not Found"
            and response_body == b""
        )

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionGET408:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        # cls.loop.set_debug(enabled=True)
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_get_408(self):
        """Test send get request w/ 408 response."""

        def request_response_cycle(host, port) -> Tuple[int, str, bytes]:
            conn = http.client.HTTPConnection(host, port)
            conn.request("GET", "/pets")
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port) -> Tuple[int, str, bytes]:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        async def agent_processing(http_connection, address) -> bool:
            # we block here to give it some time for the envelope to make it to the queue
            await asyncio.sleep(10)
            envelope = await http_connection.receive()
            is_exiting_correctly = (
                envelope is not None
                and envelope.to == address
                and len(http_connection.channel.timed_out_request_ids) == 1
            )
            return is_exiting_correctly

        client_task = asyncio.ensure_future(client_thread(self.host, self.port))
        agent_task = asyncio.ensure_future(
            agent_processing(self.http_connection, self.address)
        )

        await asyncio.gather(client_task, agent_task)
        response_status_code, response_status_text, response_body = client_task.result()
        is_exiting_correctly = agent_task.result()

        assert (
            response_status_code == 408
            and response_status_text == "Request Timeout"
            and response_body == b""
        )
        assert is_exiting_correctly

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionGET200:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        # cls.loop.set_debug(enabled=True)
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_get_200(self):
        """Test send get request w/ 200 response."""

        def request_response_cycle(host, port) -> Tuple[int, str, bytes]:
            conn = http.client.HTTPConnection(host, port)
            conn.request("GET", "/pets")
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port) -> Tuple[int, str, bytes]:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        async def agent_processing(http_connection) -> bool:
            # we block here to give it some time for the envelope to make it to the queue
            await asyncio.sleep(1)
            envelope = await http_connection.receive()
            if envelope is not None:
                incoming_message = cast(
                    HttpMessage, HttpSerializer().decode(envelope.message)
                )
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
                    message=HttpSerializer().encode(message),
                )
                await http_connection.send(response_envelope)
                is_exiting_correctly = True
            else:
                is_exiting_correctly = False
            return is_exiting_correctly

        client_task = asyncio.ensure_future(client_thread(self.host, self.port))
        agent_task = asyncio.ensure_future(agent_processing(self.http_connection))

        await asyncio.gather(client_task, agent_task)
        response_status_code, response_status_text, response_body = client_task.result()
        is_exiting_correctly = agent_task.result()

        assert (
            response_status_code == 200
            and response_status_text == "Success"
            and response_body == b"Response body"
        )
        assert is_exiting_correctly

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionPOST404:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_post_404(self):
        """Test send post request w/ 404 response."""

        def request_response_cycle(host, port):
            conn = http.client.HTTPConnection(host, port)
            body = "some body"
            conn.request("POST", "/", body)
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port):
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        response_status_code, response_status_text, response_body = await client_thread(
            self.host, self.port
        )

        assert (
            response_status_code == 404
            and response_status_text == "Request Not Found"
            and response_body == b""
        )

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionPOST408:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_post_408(self):
        """Test send post request w/ 408 response."""

        def request_response_cycle(host, port):
            conn = http.client.HTTPConnection(host, port)
            body = "some body"
            conn.request("POST", "/pets", body)
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port):
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        async def agent_processing(http_connection, address) -> bool:
            # we block here to give it some time for the envelope to make it to the queue
            await asyncio.sleep(10)
            envelope = await http_connection.receive()
            is_exiting_correctly = (
                envelope is not None
                and envelope.to == address
                and len(http_connection.channel.timed_out_request_ids) == 1
            )
            return is_exiting_correctly

        client_task = asyncio.ensure_future(client_thread(self.host, self.port))
        agent_task = asyncio.ensure_future(
            agent_processing(self.http_connection, self.address)
        )

        await asyncio.gather(client_task, agent_task)
        response_status_code, response_status_text, response_body = client_task.result()
        is_exiting_correctly = agent_task.result()

        assert (
            response_status_code == 408
            and response_status_text == "Request Timeout"
            and response_body == b""
        )
        assert is_exiting_correctly

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPServerConnectionPOST201:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = get_host()
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http_server", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPServerConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.new_event_loop()
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_post_201(self):
        """Test send post request w/ 201 response."""

        def request_response_cycle(host, port) -> Tuple[int, str, bytes]:
            conn = http.client.HTTPConnection(host, port)
            conn.request("POST", "/pets")
            response = conn.getresponse()
            return response.status, response.reason, response.read()

        async def client_thread(host, port) -> Tuple[int, str, bytes]:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                functools.partial(request_response_cycle, host=host, port=port),
            )
            return result

        async def agent_processing(http_connection) -> bool:
            # we block here to give it some time for the envelope to make it to the queue
            await asyncio.sleep(1)
            envelope = await http_connection.receive()
            if envelope is not None:
                incoming_message = cast(
                    HttpMessage, HttpSerializer().decode(envelope.message)
                )
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
                    message=HttpSerializer().encode(message),
                )
                await http_connection.send(response_envelope)
                is_exiting_correctly = True
            else:
                is_exiting_correctly = False
            return is_exiting_correctly

        client_task = asyncio.ensure_future(client_thread(self.host, self.port))
        agent_task = asyncio.ensure_future(agent_processing(self.http_connection))

        await asyncio.gather(client_task, agent_task)
        response_status_code, response_status_text, response_body = client_task.result()
        is_exiting_correctly = agent_task.result()

        assert (
            response_status_code == 201
            and response_status_text == "Created"
            and response_body == b"Response body"
        )
        assert is_exiting_correctly

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None

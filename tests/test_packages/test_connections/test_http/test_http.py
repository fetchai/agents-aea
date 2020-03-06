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

"""This module contains the tests of the gym connection module."""

import asyncio
import concurrent.futures
import http.client
import logging
import os

# import json
# from typing import Tuple
from threading import Thread

import pytest

from aea.configurations.base import ConnectionConfig, PublicId
from aea.mail.base import Envelope

from packages.fetchai.connections.http.connection import HTTPConnection

from ....conftest import ROOT_DIR, get_unused_tcp_port

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestHTTPConnectionConnectDisconnect:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class and test connect."""

        cls.address = "my_key"
        cls.host = "127.0.0.1"
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPConnection(
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
class TestHTTPConnectionSend:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = "127.0.0.1"
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPConnection(
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
    async def test_send_connection(self):
        """Test send connection error."""
        client_id = "to_key"
        envelope = Envelope(
            to=client_id,
            sender="from_key",
            protocol_id=self.protocol_id,
            message=b"some message",
        )
        await self.http_connection.send(envelope)
        assert (
            self.http_connection.channel.dispatch_ready_envelopes.get(client_id)
            == envelope
        )

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        loop = asyncio.get_event_loop()
        value = loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPConnectionGET:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = "127.0.0.1"
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.get_event_loop()
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

        cls.t = Thread(target=cls.loop.run_forever)
        cls.t.start()

    @pytest.mark.asyncio
    async def test_get_404(self):
        """Test send connection error."""

        def request_response_cycle():
            conn = http.client.HTTPConnection(self.host, self.port)
            conn.request("GET", "/")
            response = conn.getresponse()
            return response.status, response.read()

        async def client_thread():
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, request_response_cycle)
            return result

        response_code, response_body = await client_thread()

        assert response_code == 404 and response_body == b"Request Not Found"

    @pytest.mark.asyncio
    async def test_get_408(self):
        """Test get 408."""

        def request_response_cycle():
            conn = http.client.HTTPConnection(self.host, self.port)
            conn.request("GET", "/pets")
            response = conn.getresponse()
            return response.status, response.read()

        async def client_thread():
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, request_response_cycle)
            return result

        response_code, response_body = await client_thread()

        assert response_code == 408 and response_body == b"Request Timeout"

        envelope = await self.http_connection.receive()
        assert (
            envelope is not None
            and envelope.to == self.address
            and len(self.http_connection.channel.timed_out_request_ids) == 1
        )

    # @pytest.mark.asyncio
    # async def test_get_202(self):
    #     """Test send connection error."""

    #     def request_response_cycle() -> Tuple[int, bytes]:
    #         conn = http.client.HTTPConnection(self.host, self.port)
    #         conn.request("GET", "/pets")
    #         response = conn.getresponse()
    #         return response.status, response.read()

    #     async def client_thread() -> Tuple[int, bytes]:
    #         executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    #         loop = asyncio.get_event_loop()
    #         result = await loop.run_in_executor(executor, request_response_cycle)
    #         return result

    #     response_code, response_body = await client_thread()

    #     async def agent_processing() -> None:
    #         # we block here to give it some time for the envelope to make it to the queue
    #         await asyncio.sleep(1)
    #         envelope = await self.http_connection.receive()
    #         if envelope is not None:
    #             response_envelope = Envelope(
    #                 to=envelope.sender,
    #                 sender=envelope.to,
    #                 protocol_id=envelope.protocol_id,
    #                 context=envelope.context,
    #                 message=json.dumps({"status_code": 200, "message": "Response"}).encode(),
    #             )
    #         await self.http_connection.send(response_envelope)

    #     agent_processing()

    #     assert response_code == 200 and b"Response"

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        cls.loop.call_soon_threadsafe(cls.loop.stop())
        cls.t.join()
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


@pytest.mark.asyncio
class TestHTTPConnectionPOST:
    """Test the packages/fetchai/connection/http/connection.py."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""

        cls.address = "my_key"
        cls.host = "127.0.0.1"
        cls.port = get_unused_tcp_port()
        cls.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        cls.connection_id = PublicId("fetchai", "http", "0.1.0")
        cls.protocol_id = PublicId("fetchai", "http", "0.1.0")

        cls.http_connection = HTTPConnection(
            address=cls.address,
            host=cls.host,
            port=cls.port,
            api_spec_path=cls.api_spec_path,
            connection_id=cls.connection_id,
            restricted_to_protocols=set([cls.protocol_id]),
        )
        cls.loop = asyncio.get_event_loop()
        cls.http_connection.loop = cls.loop
        value = cls.loop.run_until_complete(cls.http_connection.connect())
        assert value is None
        assert cls.http_connection.connection_status.is_connected
        assert not cls.http_connection.channel.is_stopped

    @pytest.mark.asyncio
    async def test_post_404(self):
        """Test post 404."""

        def request_response_cycle():
            conn = http.client.HTTPConnection(self.host, self.port)
            body = "some body"
            conn.request("POST", "/", body)
            response = conn.getresponse()
            return response.status, response.read()

        async def client_thread():
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, request_response_cycle)
            return result

        response_code, response_body = await client_thread()

        assert response_code == 404 and response_body == b"Request Not Found"

    @pytest.mark.asyncio
    async def test_post_408(self):
        """Test post 408."""

        def request_response_cycle():
            conn = http.client.HTTPConnection(self.host, self.port)
            body = "some body"
            conn.request("POST", "/pets", body)
            response = conn.getresponse()
            return response.status, response.read()

        async def client_thread():
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, request_response_cycle)
            return result

        response_code, response_body = await client_thread()

        assert response_code == 408 and response_body == b"Request Timeout"

        envelope = await self.http_connection.receive()
        assert (
            envelope is not None
            and envelope.to == self.address
            and len(self.http_connection.channel.timed_out_request_ids) == 1
        )

    @classmethod
    def teardown_class(cls):
        """Teardown the class."""
        value = cls.loop.run_until_complete(cls.http_connection.disconnect())
        assert value is None


def test_gym_from_config():
    """Test the Connection from config File."""
    conf = ConnectionConfig()
    conf.config["api_spec_path"] = os.path.join(
        ROOT_DIR, "tests", "data", "petstore_sim.yaml"
    )
    conf.config["host"] = "127.0.0.1"
    conf.config["port"] = get_unused_tcp_port()
    conf.config["restricted_to_protocols"] = set(["fetchai/http:0.1.0"])
    con = HTTPConnection.from_config(address="my_key", connection_configuration=conf)
    assert con is not None
    assert not con.connection_status.is_connected

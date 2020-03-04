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
import logging
import os

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
class TestHTTPConnection:
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

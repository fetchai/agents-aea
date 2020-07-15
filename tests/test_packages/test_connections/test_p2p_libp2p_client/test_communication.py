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

"""This test module contains tests for Libp2p tcp client connection."""

import os
import shutil
import tempfile

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.connections.p2p_libp2p_client.connection import Uri

from tests.conftest import (
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
    skip_test_windows,
)

DEFAULT_PORT = 10234
DEFAULT_DELEGATE_PORT = 11234
DEFAULT_HOST = "127.0.0.1"
DEFAULT_CLIENTS_PER_NODE = 4


@skip_test_windows
@pytest.mark.asyncio
class TestLibp2pClientConnectionConnectDisconnect:
    """Test that connection is established and torn down correctly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.connection_node = _make_libp2p_connection(delegate=True)
        cls.connection = _make_libp2p_client_connection()

    @pytest.mark.asyncio
    async def test_libp2pclientconnection_connect_disconnect(self):
        assert self.connection.connection_status.is_connected is False
        try:
            await self.connection_node.connect()
            await self.connection.connect()
            assert self.connection.connection_status.is_connected is True
        except Exception as e:
            await self.connection.disconnect()
            raise e

        await self.connection.disconnect()
        assert self.connection.connection_status.is_connected is False
        await self.connection_node.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestLibp2pClientConnectionEchoEnvelope:
    """Test that connection will route envelope to destination through the same libp2p node"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.connection_node = _make_libp2p_connection(DEFAULT_PORT + 1, delegate=True)
        cls.multiplexer_node = Multiplexer([cls.connection_node])
        cls.log_files.append(cls.connection_node.node.log_file)
        cls.multiplexer_node.connect()

        cls.connection_client_1 = _make_libp2p_client_connection()
        cls.multiplexer_client_1 = Multiplexer([cls.connection_client_1])
        cls.multiplexer_client_1.connect()

        cls.connection_client_2 = _make_libp2p_client_connection()
        cls.multiplexer_client_2 = Multiplexer([cls.connection_client_2])
        cls.multiplexer_client_2.connect()

    def test_connection_is_established(self):
        assert self.connection_client_1.connection_status.is_connected is True
        assert self.connection_client_2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection_client_1.address
        addr_2 = self.connection_client_2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(envelope)
        delivered_envelope = self.multiplexer_client_2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message == envelope.message

    def test_envelope_echoed_back(self):
        addr_1 = self.connection_client_1.address
        addr_2 = self.connection_client_2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        original_envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(original_envelope)
        delivered_envelope = self.multiplexer_client_2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_2

        self.multiplexer_client_2.put(delivered_envelope)
        echoed_envelope = self.multiplexer_client_1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message == original_envelope.message

    def test_envelope_echoed_back_node_agent(self):
        addr_1 = self.connection_client_1.address
        addr_n = self.connection_node.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        original_envelope = Envelope(
            to=addr_n,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(original_envelope)
        delivered_envelope = self.multiplexer_node.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_n

        self.multiplexer_node.put(delivered_envelope)
        echoed_envelope = self.multiplexer_client_1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message == original_envelope.message

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer_client_1.disconnect()
        cls.multiplexer_client_2.disconnect()
        cls.multiplexer_node.disconnect()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestLibp2pClientConnectionEchoEnvelopeTwoDHTNode:
    """Test that connection will route envelope to destination connected to different node"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.connection_node_1 = _make_libp2p_connection(
            port=DEFAULT_PORT + 1,
            delegate_port=DEFAULT_DELEGATE_PORT + 1,
            delegate=True,
        )
        cls.multiplexer_node_1 = Multiplexer([cls.connection_node_1])
        cls.log_files.append(cls.connection_node_1.node.log_file)
        cls.multiplexer_node_1.connect()

        genesis_peer = cls.connection_node_1.node.multiaddrs[0]

        cls.connection_node_2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            delegate_port=DEFAULT_DELEGATE_PORT + 2,
            entry_peers=[genesis_peer],
            delegate=True,
        )
        cls.multiplexer_node_2 = Multiplexer([cls.connection_node_2])
        cls.log_files.append(cls.connection_node_2.node.log_file)
        cls.multiplexer_node_2.connect()

        cls.connection_client_1 = _make_libp2p_client_connection(
            DEFAULT_DELEGATE_PORT + 1
        )
        cls.multiplexer_client_1 = Multiplexer([cls.connection_client_1])
        cls.multiplexer_client_1.connect()

        cls.connection_client_2 = _make_libp2p_client_connection(
            DEFAULT_DELEGATE_PORT + 2
        )
        cls.multiplexer_client_2 = Multiplexer([cls.connection_client_2])
        cls.multiplexer_client_2.connect()

    def test_connection_is_established(self):
        assert self.connection_node_1.connection_status.is_connected is True
        assert self.connection_node_2.connection_status.is_connected is True
        assert self.connection_client_1.connection_status.is_connected is True
        assert self.connection_client_2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection_client_1.address
        addr_2 = self.connection_client_2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(envelope)
        delivered_envelope = self.multiplexer_client_2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message == envelope.message

    def test_envelope_echoed_back(self):
        addr_1 = self.connection_client_1.address
        addr_2 = self.connection_client_2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        original_envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(original_envelope)
        delivered_envelope = self.multiplexer_client_2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_2

        self.multiplexer_client_2.put(delivered_envelope)
        echoed_envelope = self.multiplexer_client_1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message == original_envelope.message

    def test_envelope_echoed_back_node_agent(self):
        addr_1 = self.connection_client_1.address
        addr_n = self.connection_node_2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        original_envelope = Envelope(
            to=addr_n,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_client_1.put(original_envelope)
        delivered_envelope = self.multiplexer_node_2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_n

        self.multiplexer_node_2.put(delivered_envelope)
        echoed_envelope = self.multiplexer_client_1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message == original_envelope.message

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer_client_1.disconnect()
        cls.multiplexer_client_2.disconnect()
        cls.multiplexer_node_1.disconnect()
        cls.multiplexer_node_2.disconnect()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestLibp2pClientConnectionRouting:
    """Test that libp2p DHT network will reliably route envelopes from clients connected to different nodes"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.connection_node_1 = _make_libp2p_connection(
            port=DEFAULT_PORT + 1,
            delegate_port=DEFAULT_DELEGATE_PORT + 1,
            delegate=True,
        )
        cls.multiplexer_node_1 = Multiplexer([cls.connection_node_1])
        cls.log_files.append(cls.connection_node_1.node.log_file)
        cls.multiplexer_node_1.connect()

        entry_peer = cls.connection_node_1.node.multiaddrs[0]

        cls.connection_node_2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            delegate_port=DEFAULT_DELEGATE_PORT + 2,
            entry_peers=[entry_peer],
            delegate=True,
        )
        cls.multiplexer_node_2 = Multiplexer([cls.connection_node_2])
        cls.log_files.append(cls.connection_node_2.node.log_file)
        cls.multiplexer_node_2.connect()

        cls.connections = [cls.connection_node_1, cls.connection_node_2]
        cls.multiplexers = [cls.multiplexer_node_1, cls.multiplexer_node_2]
        cls.addresses = [
            cls.connection_node_1.address,
            cls.connection_node_2.address,
        ]

        for _ in range(DEFAULT_CLIENTS_PER_NODE):
            for port in [DEFAULT_DELEGATE_PORT + 1, DEFAULT_DELEGATE_PORT + 2]:
                conn = _make_libp2p_client_connection(port)
                muxer = Multiplexer([conn])

                cls.connections.append(conn)
                cls.multiplexers.append(muxer)
                cls.addresses.append(conn.address)

                muxer.connect()

    def test_connection_is_established(self):
        for conn in self.connections:
            assert conn.connection_status.is_connected is True

    def test_star_routing_connectivity(self):
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )

        for source in range(len(self.multiplexers)):
            for destination in range(len(self.multiplexers)):
                if destination == source:
                    continue
                envelope = Envelope(
                    to=self.addresses[destination],
                    sender=self.addresses[source],
                    protocol_id=DefaultMessage.protocol_id,
                    message=DefaultSerializer().encode(msg),
                )

                self.multiplexers[source].put(envelope)
                delivered_envelope = self.multiplexers[destination].get(
                    block=True, timeout=10
                )

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message == envelope.message

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for multiplexer in reversed(cls.multiplexers):
            multiplexer.disconnect()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
def test_libp2pclientconnection_uri():
    uri = Uri(host="127.0.0.1")
    uri = Uri(host="127.0.0.1", port=10000)
    assert uri.host == "127.0.0.1" and uri.port == 10000

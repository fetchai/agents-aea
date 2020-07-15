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

"""This test module contains tests for P2PLibp2p connection."""

import os
import shutil
import tempfile

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage

from packages.fetchai.connections.p2p_libp2p.connection import Uri

from tests.conftest import (
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
    skip_test_windows,
)

DEFAULT_PORT = 10234
DEFAULT_NET_SIZE = 4


@skip_test_windows
@pytest.mark.asyncio
class TestP2PLibp2pConnectionConnectDisconnect:
    """Test that connection is established and torn down correctly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.connection = _make_libp2p_connection()

    @pytest.mark.asyncio
    async def test_p2plibp2pconnection_connect_disconnect(self):
        assert self.connection.connection_status.is_connected is False
        try:
            await self.connection.connect()
            assert self.connection.connection_status.is_connected is True
        except Exception as e:
            await self.connection.disconnect()
            raise e

        await self.connection.disconnect()
        assert self.connection.connection_status.is_connected is False

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
class TestP2PLibp2pConnectionEchoEnvelope:
    """Test that connection will route envelope to destination"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.connection1 = _make_libp2p_connection(DEFAULT_PORT + 1)
        cls.multiplexer1 = Multiplexer([cls.connection1])
        cls.log_files.append(cls.connection1.node.log_file)
        cls.multiplexer1.connect()

        genesis_peer = cls.connection1.node.multiaddrs[0]

        cls.connection2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 2, entry_peers=[genesis_peer]
        )
        cls.multiplexer2 = Multiplexer([cls.connection2])
        cls.log_files.append(cls.connection2.node.log_file)
        cls.multiplexer2.connect()

    def test_connection_is_established(self):
        assert self.connection1.connection_status.is_connected is True
        assert self.connection2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection1.node.address
        addr_2 = self.connection2.node.address

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
            message=msg,
        )

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message != envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        assert envelope.message == msg

    def test_envelope_echoed_back(self):
        addr_1 = self.connection1.node.address
        addr_2 = self.connection2.node.address

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
            message=msg,
        )

        self.multiplexer1.put(original_envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_2

        self.multiplexer2.put(delivered_envelope)
        echoed_envelope = self.multiplexer1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message != original_envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        assert original_envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRouting:
    """Test that libp2p node will reliably route envelopes in a local network"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        port_genesis = DEFAULT_PORT + 10
        cls.connection_genesis = _make_libp2p_connection(port_genesis)
        cls.multiplexer_genesis = Multiplexer([cls.connection_genesis])
        cls.log_files.append(cls.connection_genesis.node.log_file)
        cls.multiplexer_genesis.connect()

        genesis_peer = cls.connection_genesis.node.multiaddrs[0]

        cls.connections = [cls.connection_genesis]
        cls.multiplexers = [cls.multiplexer_genesis]

        port = port_genesis
        for _ in range(DEFAULT_NET_SIZE):
            port += 1
            conn = _make_libp2p_connection(port=port, entry_peers=[genesis_peer])
            muxer = Multiplexer([conn])

            cls.connections.append(conn)
            cls.multiplexers.append(muxer)

            cls.log_files.append(conn.node.log_file)
            muxer.connect()

    def test_connection_is_established(self):
        assert self.connection_genesis.connection_status.is_connected is True
        for conn in self.connections:
            assert conn.connection_status.is_connected is True

    def test_star_routing_connectivity(self):
        addrs = [conn.node.address for conn in self.connections]

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
                    to=addrs[destination],
                    sender=addrs[source],
                    protocol_id=DefaultMessage.protocol_id,
                    message=msg,
                )

                self.multiplexers[source].put(envelope)
                delivered_envelope = self.multiplexers[destination].get(
                    block=True, timeout=10
                )

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                assert envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for multiplexer in cls.multiplexers:
            multiplexer.disconnect()
        cls.multiplexer_genesis.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionEchoEnvelopeRelayOneDHTNode:
    """Test that connection will route envelope to destination using the same relay node"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.relay = _make_libp2p_connection(DEFAULT_PORT + 1)
        cls.multiplexer = Multiplexer([cls.relay])
        cls.log_files.append(cls.relay.node.log_file)
        cls.multiplexer.connect()

        relay_peer = cls.relay.node.multiaddrs[0]

        cls.connection1 = _make_libp2p_connection(
            DEFAULT_PORT + 2, relay=False, entry_peers=[relay_peer]
        )
        cls.multiplexer1 = Multiplexer([cls.connection1])
        cls.log_files.append(cls.connection1.node.log_file)
        cls.multiplexer1.connect()

        cls.connection2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 3, entry_peers=[relay_peer]
        )
        cls.multiplexer2 = Multiplexer([cls.connection2])
        cls.log_files.append(cls.connection2.node.log_file)
        cls.multiplexer2.connect()

    def test_connection_is_established(self):
        assert self.relay.connection_status.is_connected is True
        assert self.connection1.connection_status.is_connected is True
        assert self.connection2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection1.node.address
        addr_2 = self.connection2.node.address

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
            message=msg,
        )

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message != envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        assert envelope.message == msg

    def test_envelope_echoed_back(self):
        addr_1 = self.connection1.node.address
        addr_2 = self.connection2.node.address

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
            message=msg,
        )

        self.multiplexer1.put(original_envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = addr_1
        delivered_envelope.sender = addr_2

        self.multiplexer2.put(delivered_envelope)
        echoed_envelope = self.multiplexer1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == original_envelope.sender
        assert delivered_envelope.sender == original_envelope.to
        assert delivered_envelope.protocol_id == original_envelope.protocol_id
        assert delivered_envelope.message != original_envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        assert original_envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer1.disconnect()
        cls.multiplexer2.disconnect()
        cls.multiplexer.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRoutingRelayTwoDHTNodes:
    """Test that libp2p DHT network will reliably route envelopes from relay/non-relay to relay/non-relay nodes"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        port_relay_1 = DEFAULT_PORT + 10
        cls.connection_relay_1 = _make_libp2p_connection(port_relay_1)
        cls.multiplexer_relay_1 = Multiplexer([cls.connection_relay_1])
        cls.log_files.append(cls.connection_relay_1.node.log_file)
        cls.multiplexer_relay_1.connect()

        relay_peer_1 = cls.connection_relay_1.node.multiaddrs[0]

        port_relay_2 = DEFAULT_PORT + 100
        cls.connection_relay_2 = _make_libp2p_connection(
            port=port_relay_2, entry_peers=[relay_peer_1]
        )
        cls.multiplexer_relay_2 = Multiplexer([cls.connection_relay_2])
        cls.log_files.append(cls.connection_relay_2.node.log_file)
        cls.multiplexer_relay_2.connect()

        relay_peer_2 = cls.connection_relay_2.node.multiaddrs[0]

        cls.connections = [cls.connection_relay_1, cls.connection_relay_2]
        cls.multiplexers = [cls.multiplexer_relay_1, cls.multiplexer_relay_2]

        port = port_relay_1
        for _ in range(int(DEFAULT_NET_SIZE / 2) + 1):
            port += 1
            conn = _make_libp2p_connection(
                port=port, relay=False, entry_peers=[relay_peer_1]
            )
            muxer = Multiplexer([conn])
            cls.connections.append(conn)
            cls.multiplexers.append(muxer)
            cls.log_files.append(conn.node.log_file)
            muxer.connect()

        port = port_relay_2
        for _ in range(int(DEFAULT_NET_SIZE / 2) + 1):
            port += 1
            conn = _make_libp2p_connection(
                port=port, relay=False, entry_peers=[relay_peer_2]
            )
            muxer = Multiplexer([conn])
            cls.connections.append(conn)
            cls.multiplexers.append(muxer)
            cls.log_files.append(conn.node.log_file)
            muxer.connect()

    def test_connection_is_established(self):
        assert self.connection_relay_1.connection_status.is_connected is True
        assert self.connection_relay_2.connection_status.is_connected is True
        for conn in self.connections:
            assert conn.connection_status.is_connected is True

    def test_star_routing_connectivity(self):
        addrs = [conn.node.address for conn in self.connections]

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
                    to=addrs[destination],
                    sender=addrs[source],
                    protocol_id=DefaultMessage.protocol_id,
                    message=msg,
                )

                self.multiplexers[source].put(envelope)
                delivered_envelope = self.multiplexers[destination].get(
                    block=True, timeout=10
                )

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                assert envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for multiplexer in cls.multiplexers:
            multiplexer.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
def test_libp2pconnection_uri():
    uri = Uri(host="127.0.0.1")
    uri = Uri(host="127.0.0.1", port=10000)
    assert uri.host == "127.0.0.1" and uri.port == 10000

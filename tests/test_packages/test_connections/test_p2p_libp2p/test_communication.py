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

from packages.fetchai.connections.p2p_libp2p.connection import Uri
from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import (
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234
DEFAULT_NET_SIZE = 4


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
        """Test connect then disconnect."""
        assert self.connection.is_connected is False
        try:
            await self.connection.connect()
            assert self.connection.is_connected is True
        except Exception as e:
            await self.connection.disconnect()
            raise e

        await self.connection.disconnect()
        assert self.connection.is_connected is False

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


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
        cls.multiplexers = []

        try:
            cls.connection1 = _make_libp2p_connection(DEFAULT_PORT + 1)
            cls.multiplexer1 = Multiplexer([cls.connection1])
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            genesis_peer = cls.connection1.node.multiaddrs[0]

            cls.connection2 = _make_libp2p_connection(
                port=DEFAULT_PORT + 2, entry_peers=[genesis_peer]
            )
            cls.multiplexer2 = Multiplexer([cls.connection2])
            cls.log_files.append(cls.connection2.node.log_file)
            cls.multiplexer2.connect()
            cls.multiplexers.append(cls.multiplexer2)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.connection1.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed(self):
        """Test envelope routed."""
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
        msg.to = delivered_envelope.to
        msg.sender = delivered_envelope.sender
        assert envelope.message == msg

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""
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
        assert original_envelope.message_bytes == delivered_envelope.message_bytes

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


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
        cls.multiplexers = []

        try:
            port_genesis = DEFAULT_PORT + 10
            cls.connection_genesis = _make_libp2p_connection(port_genesis)
            cls.multiplexer_genesis = Multiplexer([cls.connection_genesis])
            cls.log_files.append(cls.connection_genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.connection_genesis.node.multiaddrs[0]

            cls.connections = [cls.connection_genesis]

            port = port_genesis
            for _ in range(DEFAULT_NET_SIZE):
                port += 1
                conn = _make_libp2p_connection(port=port, entry_peers=[genesis_peer])
                mux = Multiplexer([conn])

                cls.connections.append(conn)

                cls.log_files.append(conn.node.log_file)
                mux.connect()
                cls.multiplexers.append(mux)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.connection_genesis.is_connected is True
        for conn in self.connections:
            assert conn.is_connected is True

    def test_star_routing_connectivity(self):
        """Test star routing connectivity."""
        addrs = [conn.node.address for conn in self.connections]

        for source in range(len(self.multiplexers)):
            for destination in range(len(self.multiplexers)):
                if destination == source:
                    continue
                msg = DefaultMessage(
                    dialogue_reference=("", ""),
                    message_id=1,
                    target=0,
                    performative=DefaultMessage.Performative.BYTES,
                    content=b"hello",
                )
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
                msg.to = delivered_envelope.to
                msg.sender = delivered_envelope.sender
                assert envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


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
        cls.multiplexers = []

        try:
            cls.relay = _make_libp2p_connection(DEFAULT_PORT + 1)
            cls.multiplexer = Multiplexer([cls.relay])
            cls.log_files.append(cls.relay.node.log_file)
            cls.multiplexer.connect()
            cls.multiplexers.append(cls.multiplexer)

            relay_peer = cls.relay.node.multiaddrs[0]

            cls.connection1 = _make_libp2p_connection(
                DEFAULT_PORT + 2, relay=False, entry_peers=[relay_peer]
            )
            cls.multiplexer1 = Multiplexer([cls.connection1])
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            cls.connection2 = _make_libp2p_connection(
                port=DEFAULT_PORT + 3, entry_peers=[relay_peer]
            )
            cls.multiplexer2 = Multiplexer([cls.connection2])
            cls.log_files.append(cls.connection2.node.log_file)
            cls.multiplexer2.connect()
            cls.multiplexers.append(cls.multiplexer2)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.relay.is_connected is True
        assert self.connection1.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed(self):
        """Test envelope routed."""
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
        msg.to = delivered_envelope.to
        msg.sender = delivered_envelope.sender
        assert envelope.message == msg

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""
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
        assert original_envelope.message_bytes == delivered_envelope.message_bytes

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


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
        cls.multiplexers = []

        try:
            port_relay_1 = DEFAULT_PORT + 10
            cls.connection_relay_1 = _make_libp2p_connection(port_relay_1)
            cls.multiplexer_relay_1 = Multiplexer([cls.connection_relay_1])
            cls.log_files.append(cls.connection_relay_1.node.log_file)
            cls.multiplexer_relay_1.connect()
            cls.multiplexers.append(cls.multiplexer_relay_1)

            relay_peer_1 = cls.connection_relay_1.node.multiaddrs[0]

            port_relay_2 = DEFAULT_PORT + 100
            cls.connection_relay_2 = _make_libp2p_connection(
                port=port_relay_2, entry_peers=[relay_peer_1]
            )
            cls.multiplexer_relay_2 = Multiplexer([cls.connection_relay_2])
            cls.log_files.append(cls.connection_relay_2.node.log_file)
            cls.multiplexer_relay_2.connect()
            cls.multiplexers.append(cls.multiplexer_relay_2)

            relay_peer_2 = cls.connection_relay_2.node.multiaddrs[0]

            cls.connections = [cls.connection_relay_1, cls.connection_relay_2]

            port = port_relay_1
            for _ in range(int(DEFAULT_NET_SIZE / 2) + 1):
                port += 1
                conn = _make_libp2p_connection(
                    port=port, relay=False, entry_peers=[relay_peer_1]
                )
                mux = Multiplexer([conn])
                cls.connections.append(conn)
                cls.log_files.append(conn.node.log_file)
                mux.connect()
                cls.multiplexers.append(mux)

            port = port_relay_2
            for _ in range(int(DEFAULT_NET_SIZE / 2) + 1):
                port += 1
                conn = _make_libp2p_connection(
                    port=port, relay=False, entry_peers=[relay_peer_2]
                )
                mux = Multiplexer([conn])
                cls.connections.append(conn)
                cls.log_files.append(conn.node.log_file)
                mux.connect()
                cls.multiplexers.append(mux)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.connection_relay_1.is_connected is True
        assert self.connection_relay_2.is_connected is True
        for conn in self.connections:
            assert conn.is_connected is True

    def test_star_routing_connectivity(self):
        """Test star routing connectivity."""
        addrs = [conn.node.address for conn in self.connections]

        for source in range(len(self.multiplexers)):
            for destination in range(len(self.multiplexers)):
                if destination == source:
                    continue
                msg = DefaultMessage(
                    dialogue_reference=("", ""),
                    message_id=1,
                    target=0,
                    performative=DefaultMessage.Performative.BYTES,
                    content=b"hello",
                )
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
                msg.sender = delivered_envelope.sender
                msg.to = delivered_envelope.to
                assert envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


def test_libp2pconnection_uri():
    """Test uri."""
    uri = Uri(host="127.0.0.1")
    uri = Uri(host="127.0.0.1", port=10000)
    assert uri.host == "127.0.0.1" and uri.port == 10000

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
import time
from typing import Optional, Sequence

import pytest

from aea.crypto.fetchai import FetchAICrypto
from aea.mail.base import Envelope, Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.connections.p2p_libp2p.connection import (
    MultiAddr,
    P2PLibp2pConnection,
    Uri,
)

from ....conftest import skip_test_windows

DEFAULT_PORT = 10234
DEFAULT_HOST = "127.0.0.1"
DEFAULT_NET_SIZE = 4


def _make_libp2p_connection(
    port: Optional[int] = DEFAULT_PORT,
    host: Optional[str] = DEFAULT_HOST,
    relay: Optional[bool] = True,
    entry_peers: Optional[Sequence[MultiAddr]] = None,
) -> P2PLibp2pConnection:
    log_file = "libp2p_node_{}.log".format(port)
    if os.path.exists(log_file):
        os.remove(log_file)
    if relay:
        return P2PLibp2pConnection(
            FetchAICrypto().address,
            FetchAICrypto(),
            Uri("{}:{}".format(host, port)),
            Uri("{}:{}".format(host, port)),
            entry_peers=entry_peers,
            log_file=log_file,
        )
    else:
        return P2PLibp2pConnection(
            FetchAICrypto().address,
            FetchAICrypto(),
            Uri("{}:{}".format(host, port)),
            entry_peers=entry_peers,
            log_file=log_file,
        )


@skip_test_windows
@pytest.mark.asyncio
class TestP2PLibp2pConnectionConnectDisconnect:
    """Test that connection will route envelope to destination"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)
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
class TestP2PLibp2pConnectionEchoEnvelope:
    """Test that connection will route envelope to destination"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)
        cls.connection1 = _make_libp2p_connection(DEFAULT_PORT + 1)
        cls.multiplexer1 = Multiplexer([cls.connection1])
        cls.multiplexer1.connect()

        time.sleep(2)
        genesis_peer = cls.connection1.node.multiaddrs

        cls.connection2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 2, entry_peers=genesis_peer
        )
        cls.multiplexer2 = Multiplexer([cls.connection2])
        cls.multiplexer2.connect()

    def test_connection_is_established(self):
        assert self.connection1.connection_status.is_connected is True
        assert self.connection2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection1.node.agent_addr
        addr_2 = self.connection2.node.agent_addr

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

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message == envelope.message

    def test_envelope_echoed_back(self):
        addr_1 = self.connection1.node.agent_addr
        addr_2 = self.connection2.node.agent_addr

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
        assert delivered_envelope.message == original_envelope.message

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
class TestP2PLibp2pConnectionRouting:
    """Test that libp2p node will reliably route envelopes in a local network"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)
        port_genesis = DEFAULT_PORT + 10
        cls.connection_genesis = _make_libp2p_connection(port_genesis)
        cls.multiplexer_genesis = Multiplexer([cls.connection_genesis])
        cls.multiplexer_genesis.connect()

        time.sleep(2)
        genesis_peer = cls.connection_genesis.node.multiaddrs

        cls.connections = []
        cls.multiplexers = []

        port = port_genesis
        for i in range(DEFAULT_NET_SIZE):
            port += 1
            cls.connections.append(
                _make_libp2p_connection(port=port, entry_peers=genesis_peer)
            )
            cls.multiplexers.append(Multiplexer([cls.connections[i]]))
            cls.multiplexers[i].connect()

    def test_connection_is_established(self):
        for conn in self.connections:
            assert conn.connection_status.is_connected is True

    def test_star_routing_connectivity(self):
        addrs = [conn.node.agent_addr for conn in self.connections]

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
        for multiplexer in cls.multiplexers:
            multiplexer.disconnect()
        cls.multiplexer_genesis.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
class TestP2PLibp2pConnectionRelayEchoEnvelopeSameRelay:
    """Test that connection will route envelope to destination using relay"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)
        cls.relay = _make_libp2p_connection(DEFAULT_PORT + 1)
        cls.multiplexer = Multiplexer([cls.relay])
        cls.multiplexer.connect()

        time.sleep(2)
        relay_peer = cls.relay.node.multiaddrs

        cls.connection1 = _make_libp2p_connection(
            DEFAULT_PORT + 2, relay=False, entry_peers=relay_peer
        )
        cls.multiplexer1 = Multiplexer([cls.connection1])
        cls.multiplexer1.connect()

        cls.connection2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 3, entry_peers=relay_peer
        )
        cls.multiplexer2 = Multiplexer([cls.connection2])
        cls.multiplexer2.connect()

    def test_connection_is_established(self):
        assert self.relay.connection_status.is_connected is True
        assert self.connection1.connection_status.is_connected is True
        assert self.connection2.connection_status.is_connected is True

    def test_envelope_routed(self):
        addr_1 = self.connection1.node.agent_addr
        addr_2 = self.connection2.node.agent_addr

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

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message == envelope.message

    def test_envelope_echoed_back(self):
        addr_1 = self.connection1.node.agent_addr
        addr_2 = self.connection2.node.agent_addr

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
        assert delivered_envelope.message == original_envelope.message

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
class TestP2PLibp2pConnectionRelayRouting:
    """Test that libp2p DHT network will reliably route envelopes from relay/non-relay to relay/non-relay nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # os.chdir(cls.t)

        port_relay_1 = DEFAULT_PORT + 10
        cls.connection_relay_1 = _make_libp2p_connection(port_relay_1)
        cls.multiplexer_relay_1 = Multiplexer([cls.connection_relay_1])
        cls.multiplexer_relay_1.connect()

        port_relay_2 = DEFAULT_PORT + 100
        cls.connection_relay_2 = _make_libp2p_connection(port_relay_2)
        cls.multiplexer_relay_2 = Multiplexer([cls.connection_relay_2])
        cls.multiplexer_relay_2.connect()

        time.sleep(2)
        relay_peer_1 = cls.connection_relay_1.node.multiaddrs
        relay_peer_2 = cls.connection_relay_2.node.multiaddrs

        cls.connections = []
        cls.multiplexers = []

        port = port_relay_1
        for _ in range(int(DEFAULT_NET_SIZE / 2)):
            port += 1
            conn = _make_libp2p_connection(
                port=port, relay=False, entry_peers=relay_peer_1
            )
            mux = Multiplexer([conn])
            cls.connections.append(conn)
            cls.multiplexers.append(mux)
            mux.connect()

        port = port_relay_2
        for _ in range(int(DEFAULT_NET_SIZE / 2)):
            port += 1
            conn = _make_libp2p_connection(
                port=port, relay=False, entry_peers=relay_peer_2
            )
            mux = Multiplexer([conn])
            cls.connections.append(conn)
            cls.multiplexers.append(mux)
            mux.connect()

        time.sleep(2)

    def test_connection_is_established(self):
        for conn in self.connections:
            assert conn.connection_status.is_connected is True

    def skip_test_star_routing_connectivity(self):
        addrs = [conn.node.agent_addr for conn in self.connections]

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
        for multiplexer in cls.multiplexers:
            multiplexer.disconnect()
        cls.multiplexer_relay_1.disconnect()
        cls.multiplexer_relay_2.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

import asyncio
import os
from itertools import permutations
from unittest import mock
from unittest.mock import Mock, call

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.crypto.registries import make_crypto
from aea.mail.base import Empty
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.valory.connections.p2p_libp2p.connection import NodeClient, Uri

from tests.conftest import _make_libp2p_connection, libp2p_log_on_failure_all
from tests.test_packages.test_connections.test_p2p_libp2p.base import BaseP2PLibp2pTest


DEFAULT_NET_SIZE = 4

MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@pytest.mark.asyncio
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionConnectDisconnect(BaseP2PLibp2pTest):
    """Test that connection is established and torn down correctly"""

    @pytest.mark.asyncio
    async def test_p2p_libp2p_connection_connect_disconnect_default(self):
        """Test connect then disconnect."""
        connection = _make_libp2p_connection()

        assert connection.is_connected is False
        try:
            await connection.connect()
            assert connection.is_connected is True
        except Exception as e:
            await connection.disconnect()
            raise e

        await connection.disconnect()
        assert connection.is_connected is False

    @pytest.mark.asyncio
    async def test_p2p_libp2p_connection_connect_disconnect_ethereum(self):
        """Test connect then disconnect."""
        crypto = make_crypto(EthereumCrypto.identifier)
        connection = _make_libp2p_connection(agent_key=crypto)

        assert connection.is_connected is False
        try:
            await connection.connect()
            assert connection.is_connected is True
        except Exception as e:
            await connection.disconnect()
            raise e

        await connection.disconnect()
        assert connection.is_connected is False


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionEchoEnvelope(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        aea_ledger_fetchai = make_crypto(FetchAICrypto.identifier)
        aea_ledger_ethereum = make_crypto(EthereumCrypto.identifier)

        try:
            cls.connection1 = _make_libp2p_connection(agent_key=aea_ledger_fetchai)
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            genesis_peer = cls.connection1.node.multiaddrs[0]

            cls.connection2 = _make_libp2p_connection(
                entry_peers=[genesis_peer],
                agent_key=aea_ledger_ethereum,
            )
            cls.multiplexer2 = Multiplexer(
                [cls.connection2], protocols=[MockDefaultMessageProtocol]
            )
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
        addr_1 = self.connection1.address
        addr_2 = self.connection2.address

        envelope = self.enveloped_default_message(to=addr_2, sender=addr_1)
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""
        sender = self.connection1.address
        to = self.connection2.address

        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexer2.put(delivered_envelope)
        echoed_envelope = self.multiplexer1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == envelope.sender
        assert delivered_envelope.sender == envelope.to
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message != envelope.message
        assert envelope.message_bytes == delivered_envelope.message_bytes


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRouting(BaseP2PLibp2pTest):
    """Test that libp2p node will reliably route envelopes in a local network"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        try:
            cls.connection_genesis = _make_libp2p_connection()
            cls.multiplexer_genesis = Multiplexer(
                [cls.connection_genesis], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.connection_genesis.node.multiaddrs[0]

            for i in range(DEFAULT_NET_SIZE):
                conn = _make_libp2p_connection(entry_peers=[genesis_peer])
                mux = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])
                cls.log_files.append(conn.node.log_file)
                mux.connect()
                cls.multiplexers.append(mux)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_multiplexer_connections_connected

    def test_star_routing_connectivity(self):
        """Test star routing connectivity."""

        addrs = [c.address for mux in self.multiplexers for c in mux.connections]
        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            envelope = self.enveloped_default_message(to=addrs[v], sender=addrs[u])
            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=10)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionEchoEnvelopeRelayOneDHTNode(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination using the same relay node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        try:
            cls.relay = _make_libp2p_connection()
            cls.multiplexer = Multiplexer([cls.relay])
            cls.log_files.append(cls.relay.node.log_file)
            cls.multiplexer.connect()
            cls.multiplexers.append(cls.multiplexer)

            relay_peer = cls.relay.node.multiaddrs[0]

            cls.connection1 = _make_libp2p_connection(
                relay=False,
                entry_peers=[relay_peer],
            )
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)
            cls.connection2 = _make_libp2p_connection(entry_peers=[relay_peer])
            cls.multiplexer2 = Multiplexer(
                [cls.connection2], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection2.node.log_file)
            cls.multiplexer2.connect()
            cls.multiplexers.append(cls.multiplexer2)
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_multiplexer_connections_connected

    def test_envelope_routed(self):
        """Test envelope routed."""
        sender = self.connection1.address
        to = self.connection2.address

        envelope = self.enveloped_default_message(to=to, sender=sender)
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""
        sender = self.connection1.address
        to = self.connection2.address

        envelope = self.enveloped_default_message(to=to, sender=sender)
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexer2.put(delivered_envelope)
        echoed_envelope = self.multiplexer1.get(block=True, timeout=5)

        assert echoed_envelope is not None
        assert echoed_envelope.to == envelope.sender
        assert delivered_envelope.sender == envelope.to
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message != envelope.message
        assert envelope.message_bytes == delivered_envelope.message_bytes


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRoutingRelayTwoDHTNodes(BaseP2PLibp2pTest):
    """Test that libp2p DHT network will reliably route envelopes from relay/non-relay to relay/non-relay nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        def make_relay(relay_peer):
            conn = _make_libp2p_connection(
                relay=False,
                entry_peers=[relay_peer],
            )
            mux = Multiplexer([conn])
            mux.connect()
            cls.connections.append(conn)
            cls.multiplexers.append(mux)
            cls.log_files.append(conn.node.log_file)

        try:
            cls.connection_relay_1 = _make_libp2p_connection()
            cls.multiplexer_relay_1 = Multiplexer(
                [cls.connection_relay_1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_relay_1.node.log_file)
            cls.multiplexer_relay_1.connect()
            cls.multiplexers.append(cls.multiplexer_relay_1)

            relay_peer_1 = cls.connection_relay_1.node.multiaddrs[0]
            cls.connection_relay_2 = _make_libp2p_connection(entry_peers=[relay_peer_1])
            cls.multiplexer_relay_2 = Multiplexer(
                [cls.connection_relay_2], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_relay_2.node.log_file)
            cls.multiplexer_relay_2.connect()
            cls.multiplexers.append(cls.multiplexer_relay_2)

            relay_peer_2 = cls.connection_relay_2.node.multiaddrs[0]
            cls.connections = [cls.connection_relay_1, cls.connection_relay_2]

            for i in range(DEFAULT_NET_SIZE // 2 + 1):
                make_relay(relay_peer_1)
                make_relay(relay_peer_2)

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

        addrs = [conn.address for conn in self.connections]
        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            envelope = self.enveloped_default_message(to=addrs[v], sender=addrs[u])
            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=10)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


def test_libp2pconnection_uri():
    """Test uri."""
    uri = Uri(host="127.0.0.1")
    uri = Uri(host="127.0.0.1", port=10000)
    assert uri.host == "127.0.0.1" and uri.port == 10000


@pytest.mark.asyncio
class TestP2PLibp2pNodeRestart(BaseP2PLibp2pTest):
    """Test node restart."""

    @pytest.mark.asyncio
    async def test_node_restart(self):
        """Test node restart works."""
        connection = _make_libp2p_connection()
        try:
            await connection.node.start()
            pipe = connection.node.pipe
            assert pipe is not None
            await connection.node.restart()
            new_pipe = connection.node.pipe
            assert new_pipe is not None
            assert new_pipe is not pipe
        finally:
            await connection.node.stop()


@libp2p_log_on_failure_all
class BaseTestP2PLibp2p(BaseP2PLibp2pTest):
    """Base test class for p2p libp2p tests with two peers."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        aea_ledger_fetchai = make_crypto(FetchAICrypto.identifier)
        aea_ledger_ethereum = make_crypto(EthereumCrypto.identifier)

        try:
            cls.connection1 = _make_libp2p_connection(agent_key=aea_ledger_fetchai)
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            genesis_peer = cls.connection1.node.multiaddrs[0]
            cls.connection2 = _make_libp2p_connection(
                entry_peers=[genesis_peer],
                agent_key=aea_ledger_ethereum,
            )
            cls.multiplexer2 = Multiplexer(
                [cls.connection2], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection2.node.log_file)
            cls.multiplexer2.connect()
            cls.multiplexers.append(cls.multiplexer2)
        except Exception as e:
            cls.teardown_class()
            raise e


@libp2p_log_on_failure_all
class TestP2PLibp2PSendEnvelope(BaseTestP2PLibp2p):
    """Test that connection will send envelope with error, and that reconnection fixes it."""

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_multiplexer_connections_connected

    def test_envelope_routed(self):
        """Test envelope routed."""

        sender = self.connection2.address
        to = self.connection1.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        # make failure on send
        # note: we don't mock the genesis peer.
        with mock.patch.object(
            self.connection2.logger, "exception"
        ) as _mock_logger, mock.patch.object(
            self.connection2.node.pipe, "write", side_effect=Exception("some error")
        ):
            self.multiplexer2.put(envelope)
            delivered_envelope = self.multiplexer1.get(block=True, timeout=20)
            _mock_logger.assert_called_with(
                "Failed to send after pipe reconnect. Exception: some error. Try recover connection to node and send again."
            )

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestP2PLibp2PReceiveEnvelope(BaseTestP2PLibp2p):
    """Test that connection will receive envelope with error, and that reconnection fixes it."""

    def test_envelope_routed(self):
        """Test envelope routed."""

        sender = self.connection1.address
        to = self.connection2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        # make the reception fail
        with mock.patch.object(
            self.connection2.logger, "exception"
        ) as _mock_logger, mock.patch.object(
            self.connection2.node.pipe, "read", side_effect=Exception("some error")
        ):
            self.multiplexer1.put(envelope)
            delivered_envelope = self.multiplexer2.get(block=True, timeout=20)
            expected = "Failed to read. Exception: some error. Try reconnect to node and read again."
            _mock_logger.assert_has_calls([call(expected)])

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestLibp2pEnvelopeOrder(BaseTestP2PLibp2p):
    """
    Test message ordering.

    Test that the order of envelope is the guaranteed to be the same
    when communicating between two peers.
    """

    NB_ENVELOPES = 1000

    def test_burst_order(self):
        """Test order of envelope burst is guaranteed on receiving end."""

        sender = self.connection1.address
        to = self.connection2.address
        sent_envelopes = [self.enveloped_default_message(to, sender) for _ in range(self.NB_ENVELOPES)]

        for envelope in sent_envelopes:
            envelope.message = envelope.message_bytes  # encode
            self.multiplexer1.put(envelope)

        received_envelopes = []
        for _ in range(self.NB_ENVELOPES):
            envelope = self.multiplexer2.get(block=True, timeout=3)
            received_envelopes.append(envelope)

        # test no new message is "created"
        with pytest.raises(Empty):
            self.multiplexer2.get(block=True, timeout=1)

        assert len(sent_envelopes) == len(received_envelopes)
        for expected, actual in zip(sent_envelopes, received_envelopes):
            assert expected.message == actual.message


@pytest.mark.asyncio
async def test_nodeclient_pipe_connect():
    """Test pipe.connect called on NodeClient.connect."""
    f = asyncio.Future()
    f.set_result(None)
    pipe = Mock()
    pipe.connect.return_value = f
    node_client = NodeClient(pipe, Mock())
    await node_client.connect()
    pipe.connect.assert_called_once()


@pytest.mark.asyncio
async def test_write_acn_error():
    """Test pipe.connect called on NodeClient.connect."""
    f = asyncio.Future()
    f.set_result(None)
    pipe = Mock()
    pipe.write.return_value = f
    node_client = NodeClient(pipe, Mock())
    await node_client.write_acn_status_error("some message")
    pipe.write.assert_called_once()

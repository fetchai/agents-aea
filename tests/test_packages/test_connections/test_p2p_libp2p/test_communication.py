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
from itertools import permutations
from unittest import mock
from unittest.mock import Mock, call

import pytest

from aea.mail.base import Empty

from packages.valory.connections.p2p_libp2p.connection import NodeClient

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    TIMEOUT,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
)


DEFAULT_NET_SIZE = 4


@pytest.mark.asyncio
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionConnectDisconnect(BaseP2PLibp2pTest):
    """Test that connection is established and torn down correctly"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("crypto", BaseP2PLibp2pTest._cryptos)
    async def test_p2p_libp2p_connection_connect_disconnect(self, crypto):
        """Test connect then disconnect."""

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

        cls.connection1 = cls.make_connection(agent_key=cls.libp2p_crypto)
        genesis_peer = cls.connection1.node.multiaddrs[0]
        cls.connection2 = cls.make_connection(
            entry_peers=[genesis_peer],
            agent_key=cls.default_crypto,
        )

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_envelope_routed(self):
        """Test envelope routed."""

        sender = self.connection1.address
        to = self.connection2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[0].put(envelope)
        delivered_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""

        sender = self.connection1.address
        to = self.connection2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[0].put(envelope)
        delivered_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[1].put(delivered_envelope)
        echoed_envelope = self.multiplexers[0].get(block=True, timeout=TIMEOUT)

        assert echoed_envelope is not None
        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRouting(BaseP2PLibp2pTest):
    """Test that libp2p node will reliably route envelopes in a local network"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        connection_genesis = cls.make_connection()
        genesis_peer = connection_genesis.node.multiaddrs[0]
        for _ in range(DEFAULT_NET_SIZE):
            cls.make_connection(entry_peers=[genesis_peer])

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_star_routing_connectivity(self):
        """Test star routing connectivity."""

        addrs = [c.address for m in self.multiplexers for c in m.connections]
        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            envelope = self.enveloped_default_message(to=addrs[v], sender=addrs[u])
            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=TIMEOUT)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionEchoEnvelopeRelayOneDHTNode(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination using the same relay node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        relay = cls.make_connection()
        relay_peer = relay.node.multiaddrs[0]

        cls.connection1 = cls.make_connection(relay=False, entry_peers=[relay_peer])
        cls.connection2 = cls.make_connection(entry_peers=[relay_peer])

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_envelope_routed(self):
        """Test envelope routed."""

        sender = self.connection1.address
        to = self.connection2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[1].put(envelope)
        delivered_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test envelope echoed back."""

        sender = self.connection1.address
        to = self.connection2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[1].put(envelope)
        delivered_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[2].put(delivered_envelope)
        echoed_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)

        assert echoed_envelope is not None
        self.sent_is_echoed_envelope(envelope, echoed_envelope)


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRoutingRelayTwoDHTNodes(BaseP2PLibp2pTest):
    """Test DHT network routing of envelopes from relay/non-relay to relay/non-relay nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.connection1 = cls.make_connection()
        relay_peer_1 = cls.connection1.node.multiaddrs[0]
        cls.connection2 = cls.make_connection(entry_peers=[relay_peer_1])
        relay_peer_2 = cls.connection2.node.multiaddrs[0]

        for _ in range(DEFAULT_NET_SIZE // 2 + 1):
            cls.make_connection(entry_peers=[relay_peer_1])
            cls.make_connection(entry_peers=[relay_peer_2])

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_star_routing_connectivity(self):
        """Test star routing connectivity."""

        addrs = [c.address for m in self.multiplexers for c in m.connections]
        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            envelope = self.enveloped_default_message(to=addrs[v], sender=addrs[u])
            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=TIMEOUT)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@pytest.mark.asyncio
class TestP2PLibp2pNodeRestart(BaseP2PLibp2pTest):
    """Test node restart."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("crypto", BaseP2PLibp2pTest._cryptos)
    async def test_node_restart(self, crypto):
        """Test node restart works."""

        connection = _make_libp2p_connection(agent_key=crypto)
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

        cls.connection1 = cls.make_connection(agent_key=cls.libp2p_crypto)
        genesis_peer = cls.connection1.node.multiaddrs[0]
        cls.connection2 = cls.make_connection(
            entry_peers=[genesis_peer],
            agent_key=cls.default_crypto,
        )


@libp2p_log_on_failure_all
class TestP2PLibp2PSendEnvelope(BaseTestP2PLibp2p):
    """Test that connection will send envelope with error, and that reconnection fixes it."""

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_envelope_routed(self):
        """Test envelope routed."""

        sender = self.connection2.address
        to = self.connection1.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        # cause failure on send
        # note: we don't mock the genesis peer.
        with mock.patch.object(
            self.connection2.logger, "exception"
        ) as _mock_logger, mock.patch.object(
            self.connection2.node.pipe, "write", side_effect=Exception("some error")
        ):
            self.multiplexers[1].put(envelope)
            delivered_envelope = self.multiplexers[0].get(block=True, timeout=20)
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
            self.multiplexers[0].put(envelope)
            delivered_envelope = self.multiplexers[1].get(block=True, timeout=20)
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
        sent_envelopes = [
            self.enveloped_default_message(to, sender) for _ in range(self.NB_ENVELOPES)
        ]

        for envelope in sent_envelopes:
            envelope.message = envelope.message_bytes  # encode
            self.multiplexers[0].put(envelope)

        received_envelopes = []
        for _ in range(self.NB_ENVELOPES):
            envelope = self.multiplexers[1].get(block=True, timeout=3)
            received_envelopes.append(envelope)

        # test no new message is "created"
        with pytest.raises(Empty):
            self.multiplexers[1].get(block=True, timeout=1)

        assert len(sent_envelopes) == len(received_envelopes)
        for expected, actual in zip(sent_envelopes, received_envelopes):
            assert expected.message == actual.message


@pytest.mark.asyncio
async def test_node_client_pipe_connect():
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

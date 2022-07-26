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

"""This test module contains tests for Libp2p tcp client connection."""

from itertools import permutations
from unittest.mock import Mock

import pytest
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto

from aea.mail.base import Empty

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    TIMEOUT,
    _make_libp2p_connection,
    _make_libp2p_mailbox_connection,
    libp2p_log_on_failure_all,
    ports,
)


DEFAULT_CLIENTS_PER_NODE = 1

MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@pytest.mark.asyncio
class TestLibp2pMailboxConnectionConnectDisconnect(BaseP2PLibp2pTest):
    """Test that connection is established and torn down correctly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.delegate_port = next(ports)
        cls.mailbox_port = next(ports)

        cls.connection_node = _make_libp2p_connection(
            delegate=True,
            delegate_port=cls.delegate_port,
            mailbox=True,
            mailbox_port=cls.mailbox_port,
        )
        cls.connection = _make_libp2p_mailbox_connection(
            peer_public_key=cls.connection_node.node.pub,
            node_port=cls.mailbox_port,
        )

    @pytest.mark.asyncio
    async def test_libp2pclientconnection_connect_disconnect(self):
        """Test connnect then disconnect."""
        assert self.connection.is_connected is False
        try:
            await self.connection_node.connect()
            await self.connection.connect()
            assert self.connection.is_connected is True
            await self.connection.disconnect()
            assert self.connection.is_connected is False
        except Exception:
            raise
        finally:
            await self.connection_node.disconnect()


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionEchoEnvelopeTwoDHTNode(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination connected to different node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.mailbox_ports = next(ports), next(ports)

        cls.connection_node_1 = cls.make_connection(
            mailbox_port=cls.mailbox_ports[0],
            delegate=True,
            mailbox=True,
        )
        genesis_peer = cls.connection_node_1.node.multiaddrs[0]

        cls.connection_node_2 = cls.make_connection(
            mailbox_port=cls.mailbox_ports[1],
            entry_peers=[genesis_peer],
            delegate=True,
            mailbox=True,
        )

        cls.connection_client_1 = cls.make_mailbox_connection(
            peer_public_key=cls.connection_node_1.node.pub,
            node_port=cls.mailbox_ports[0],
        )
        cls.connection_client_2 = cls.make_mailbox_connection(
            peer_public_key=cls.connection_node_2.node.pub,
            node_port=cls.mailbox_ports[1],
        )

    def test_connection_is_established(self):
        """Test the connection is established."""
        assert self.all_connected

    def test_envelope_routed(self):
        """Test the envelope is routed."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[2].put(envelope)
        delivered_envelope = self.multiplexers[3].get(block=True, timeout=TIMEOUT)
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test the envelope is echoed back."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[2].put(envelope)
        delivered_envelope = self.multiplexers[3].get(block=True, timeout=TIMEOUT)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[3].put(delivered_envelope)
        echoed_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)

        self.sent_is_echoed_envelope(envelope, echoed_envelope)

    def test_envelope_echoed_back_node_agent(self):
        """Test the envelope is echoed back node agent."""

        sender = self.connection_client_1.address
        to = self.connection_node_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[2].put(envelope)
        delivered_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[1].put(delivered_envelope)
        echoed_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)
        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionRouting(BaseP2PLibp2pTest):
    """Test that libp2p DHT network will reliably route envelopes from clients connected to different nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.mailbox_ports = next(ports), next(ports)

        cls.connection_node_1 = cls.make_connection(
            port=next(ports),
            delegate_port=next(ports),
            mailbox_port=cls.mailbox_ports[0],
            delegate=True,
            mailbox=True,
        )
        entry_peer = cls.connection_node_1.node.multiaddrs[0]
        cls.connection_node_2 = cls.make_connection(
            port=next(ports),
            delegate_port=next(ports),
            mailbox_port=cls.mailbox_ports[1],
            entry_peers=[entry_peer],
            delegate=True,
            mailbox=True,
        )

        cls.addresses = [
            cls.connection_node_1.address,
            cls.connection_node_2.address,
        ]
        peers_public_keys = [
            cls.connection_node_1.node.pub,
            cls.connection_node_2.node.pub,
        ]
        for i, port in enumerate(cls.mailbox_ports):
            peer_public_key = peers_public_keys[i]
            conn = cls.make_mailbox_connection(
                peer_public_key=peer_public_key,
                node_port=port,
            )
            cls.addresses.append(conn.address)

    def test_connection_is_established(self):
        """Test connection is established."""
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
class BaseTestLibp2pClientSamePeer(BaseP2PLibp2pTest):
    """Base test class for reconnection tests."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.delegate_port = next(ports)
        cls.mailbox_port = next(ports)

        cls.connection_node = cls.make_connection(
            delegate=True,
            delegate_port=cls.delegate_port,
            mailbox=True,
            mailbox_port=cls.mailbox_port,
        )

        cls.connection_client_1 = cls.make_mailbox_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=CosmosCrypto.identifier,
            node_port=cls.mailbox_port,
        )
        cls.connection_client_2 = cls.make_mailbox_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=EthereumCrypto.identifier,
            node_port=cls.mailbox_port,
        )


@libp2p_log_on_failure_all
class TestLibp2pClientEnvelopeOrderSamePeer(BaseTestLibp2pClientSamePeer):
    """Test that the order of envelope is the guaranteed to be the same."""

    NB_ENVELOPES = 1000

    def test_burst_order(self):
        """Test order of envelope burst is guaranteed on receiving end."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        sent_envelopes = [
            self.enveloped_default_message(to, sender) for _ in range(self.NB_ENVELOPES)
        ]
        for envelope in sent_envelopes:
            envelope.message = envelope.message_bytes  # encode
            self.multiplexers[1].put(envelope)

        received_envelopes = []
        for _ in range(self.NB_ENVELOPES):
            envelope = self.multiplexers[2].get(block=True, timeout=20)
            received_envelopes.append(envelope)

        # test no new message is "created"
        with pytest.raises(Empty):
            self.multiplexers[2].get(block=True, timeout=1)

        assert len(sent_envelopes) == len(received_envelopes)
        for expected, actual in zip(sent_envelopes, received_envelopes):
            assert expected.message == actual.message

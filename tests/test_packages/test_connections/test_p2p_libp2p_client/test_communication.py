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

import time
from unittest import mock
from unittest.mock import call

import pytest

from aea.mail.base import Empty
from aea.test_tools.mocks import RegexComparator

from tests.conftest import DEFAULT_LEDGER
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    LIBP2P_LEDGER,
    TIMEOUT,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
    ports,
)
from tests.test_packages.test_connections.test_p2p_libp2p.test_communication import (
    TestP2PLibp2pConnectionRouting,
)


DEFAULT_CLIENTS_PER_NODE = 1


@pytest.mark.asyncio
@libp2p_log_on_failure_all
class TestLibp2pClientConnectionConnectDisconnect(BaseP2PLibp2pTest):
    """Test that connection is established and torn down correctly"""

    @pytest.mark.asyncio
    async def test_libp2p_client_connection_connect_disconnect(self):
        """Test connnect then disconnect."""

        delegate_port = next(ports)
        connection_node = _make_libp2p_connection(
            delegate=True, delegate_port=delegate_port
        )
        connection = _make_libp2p_client_connection(
            peer_public_key=connection_node.node.pub,
            node_port=delegate_port,
        )

        assert connection.is_connected is False
        try:
            await connection_node.connect()
            await connection.connect()
            assert connection.is_connected is True
            await connection.disconnect()
            assert connection.is_connected is False
        except Exception:
            raise
        finally:
            await connection_node.disconnect()


@pytest.mark.asyncio
@libp2p_log_on_failure_all
class TestLibp2pClientConnectionEchoEnvelope(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination through the same libp2p node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        delegate_port = next(ports)
        cls.connection_node = cls.make_connection(
            delegate=True,
            delegate_port=delegate_port,
        )

        cls.connection_client_1 = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=cls.cosmos_crypto.identifier,
            node_port=delegate_port,
        )
        cls.connection_client_2 = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=cls.ethereum_crypto.identifier,
            node_port=delegate_port,
        )

    def test_connection_is_established(self):
        """Test connection is established."""
        assert self.all_connected

    def test_envelope_routed(self):
        """Test the envelope is routed."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[1].put(envelope)
        delivered_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test the envelope is echoed back."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[1].put(envelope)
        delivered_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[2].put(delivered_envelope)
        echoed_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)
        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)

    def test_envelope_echoed_back_node_agent(self):
        """Test the envelope is echoed back."""

        sender = self.connection_client_1.address
        to = self.connection_node.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[1].put(envelope)
        delivered_envelope = self.multiplexers[0].get(block=True, timeout=TIMEOUT)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[0].put(delivered_envelope)
        echoed_envelope = self.multiplexers[1].get(block=True, timeout=TIMEOUT)
        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionEchoEnvelopeTwoDHTNode(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination connected to different node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.ports = next(ports), next(ports)

        cls.connection_node_1 = cls.make_connection(
            delegate_port=cls.ports[0],
            delegate=True,
        )
        genesis_peer = cls.connection_node_1.node.multiaddrs[0]
        cls.connection_node_2 = cls.make_connection(
            delegate_port=cls.ports[1],
            entry_peers=[genesis_peer],
            delegate=True,
        )

        cls.connection_client_1 = cls.make_client_connection(
            peer_public_key=cls.connection_node_1.node.pub,
            node_port=cls.ports[0],
        )
        cls.connection_client_2 = cls.make_client_connection(
            peer_public_key=cls.connection_node_2.node.pub,
            node_port=cls.ports[1],
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
        delivered_envelope = self.multiplexers[3].get(block=True, timeout=20)

        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_echoed_back(self):
        """Test the envelope is echoed back."""

        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[2].put(envelope)
        delivered_envelope = self.multiplexers[3].get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[3].put(delivered_envelope)
        echoed_envelope = self.multiplexers[2].get(block=True, timeout=5)
        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)

    def test_envelope_echoed_back_node_agent(self):
        """Test the envelope is echoed back node agent."""

        sender = self.connection_client_1.address
        to = self.connection_node_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexers[2].put(envelope)
        delivered_envelope = self.multiplexers[1].get(block=True, timeout=10)
        assert delivered_envelope is not None

        delivered_envelope.to = sender
        delivered_envelope.sender = to

        self.multiplexers[1].put(delivered_envelope)
        echoed_envelope = self.multiplexers[2].get(block=True, timeout=5)

        assert self.sent_is_echoed_envelope(envelope, echoed_envelope)


@libp2p_log_on_failure_all
class TestLibp2pClientConnectionRouting(TestP2PLibp2pConnectionRouting):
    """Test that libp2p DHT network will reliably route envelopes from clients connected to different nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        BaseP2PLibp2pTest.setup_class()

        cls.ports = next(ports), next(ports)
        connection1 = cls.make_connection(
            delegate_port=cls.ports[0],
            delegate=True,
        )
        entry_peer = connection1.node.multiaddrs[0]
        connection2 = cls.make_connection(
            delegate_port=cls.ports[1],
            entry_peers=[entry_peer],
            delegate=True,
        )

        peers_public_keys = [connection1.node.pub, connection2.node.pub]
        assert len(cls.ports) == len(peers_public_keys)
        for port, peer_public_key in zip(cls.ports, peers_public_keys):
            cls.make_client_connection(
                peer_public_key=peer_public_key,
                node_port=port,
            )


@libp2p_log_on_failure_all
class BaseTestLibp2pClientSamePeer(BaseP2PLibp2pTest):
    """Base test class for reconnection tests."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.delegate_port = next(ports)
        cls.connection_node = cls.make_connection(
            delegate=True,
            delegate_port=cls.delegate_port,
        )

        cls.connection_client_1 = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=LIBP2P_LEDGER,
            node_port=cls.delegate_port,
        )
        cls.connection_client_2 = cls.make_client_connection(
            peer_public_key=cls.connection_node.node.pub,
            ledger_api_id=DEFAULT_LEDGER,
            node_port=cls.delegate_port,
        )


@libp2p_log_on_failure_all
class TestLibp2pClientReconnectionSendEnvelope(BaseTestLibp2pClientSamePeer):
    """Test that connection will send envelope with error, and that reconnection fixes it."""

    def test_envelope_sent(self):
        """Test the envelope is routed."""
        sender = self.connection_client_1.address
        to = self.connection_client_2.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        # cause failure on send
        with mock.patch.object(
            self.connection_client_1.logger, "exception"
        ) as _mock_logger, mock.patch.object(
            self.connection_client_1._node_client, "_write", side_effect=Exception
        ):
            self.multiplexers[1].put(envelope)
            delivered_envelope = self.multiplexers[2].get(block=True, timeout=TIMEOUT)
            expected = "Exception raised on message send. Try reconnect and send again."
            _mock_logger.assert_has_calls([call(expected)])

        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestLibp2pClientReconnectionReceiveEnvelope(BaseTestLibp2pClientSamePeer):
    """Test that connection will receive envelope with error, and that reconnection fixes it."""

    def test_envelope_received(self):
        """Test the envelope is routed."""
        sender = self.connection_client_2.address
        to = self.connection_client_1.address
        envelope = self.enveloped_default_message(to=to, sender=sender)

        # make the reception fail
        with mock.patch.object(
            self.connection_client_1.logger, "error"
        ) as _mock_logger, mock.patch.object(
            self.connection_client_1._node_client,
            "_read",
            side_effect=ConnectionError(),
        ):
            # this envelope will be lost.
            self.multiplexers[2].put(envelope)
            time.sleep(2.0)
            expected = "Connection error:.*Try to reconnect and read again"
            _mock_logger.assert_has_calls([call(RegexComparator(expected))])

        # proceed as usual. Now we expect the connection to have reconnected successfully
        delivered_envelope = self.multiplexers[1].get(block=True, timeout=20)
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


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
            envelope = self.multiplexers[2].get(block=True, timeout=3)
            received_envelopes.append(envelope)

        # test no new message is "created"
        with pytest.raises(Empty):
            self.multiplexers[2].get(block=True, timeout=1)

        assert len(sent_envelopes) == len(received_envelopes)
        for expected, actual in zip(sent_envelopes, received_envelopes):
            assert expected.message == actual.message

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
from aea.mail.base import Empty, Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default import DefaultSerializer
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.valory.connections.p2p_libp2p.connection import NodeClient, Uri

from tests.conftest import (
    BaseP2PLibp2pTest,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
)


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
    async def test_p2plibp2pconnection_connect_disconnect_default(self):
        """Test connect then disconnect."""
        connection = _make_libp2p_connection(data_dir=self.tmp_dir)

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
    async def test_p2plibp2pconnection_connect_disconnect_ethereum(self):
        """Test connect then disconnect."""
        crypto = make_crypto(EthereumCrypto.identifier)
        connection = _make_libp2p_connection(data_dir=self.tmp_dir, agent_key=crypto)

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
            temp_dir_1 = os.path.join(cls.t, "temp_dir_1")
            cls.connection1 = _make_libp2p_connection(
                data_dir=temp_dir_1, agent_key=aea_ledger_fetchai
            )
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            genesis_peer = cls.connection1.node.multiaddrs[0]

            temp_dir_2 = os.path.join(cls.t, "temp_dir_2")
            cls.connection2 = _make_libp2p_connection(
                data_dir=temp_dir_2,
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
            message=msg,
        )
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
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
        assert (
            delivered_envelope.protocol_specification_id
            == original_envelope.protocol_specification_id
        )
        assert delivered_envelope.message != original_envelope.message
        assert original_envelope.message_bytes == delivered_envelope.message_bytes


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRouting(BaseP2PLibp2pTest):
    """Test that libp2p node will reliably route envelopes in a local network"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        try:
            temp_dir_gen = os.path.join(cls.t, "temp_dir_gen")
            cls.connection_genesis = _make_libp2p_connection(data_dir=temp_dir_gen)
            cls.multiplexer_genesis = Multiplexer(
                [cls.connection_genesis], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.connection_genesis.node.multiaddrs[0]

            cls.connections = [cls.connection_genesis]

            for i in range(DEFAULT_NET_SIZE):
                temp_dir = os.path.join(cls.t, f"temp_dir_{i}")
                conn = _make_libp2p_connection(
                    data_dir=temp_dir, entry_peers=[genesis_peer]
                )
                mux = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])

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

        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            envelope = Envelope(
                to=addrs[v],
                sender=addrs[u],
                message=msg,
            )

            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=10)

            assert delivered_envelope is not None
            assert delivered_envelope.to == envelope.to
            assert delivered_envelope.sender == envelope.sender
            assert (
                delivered_envelope.protocol_specification_id
                == envelope.protocol_specification_id
            )
            assert delivered_envelope.message != envelope.message
            msg = DefaultMessage.serializer.decode(delivered_envelope.message)
            msg.to = delivered_envelope.to
            msg.sender = delivered_envelope.sender
            assert envelope.message == msg


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionEchoEnvelopeRelayOneDHTNode(BaseP2PLibp2pTest):
    """Test that connection will route envelope to destination using the same relay node"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        try:
            temp_dir_rel = os.path.join(cls.t, "temp_dir_rel")
            cls.relay = _make_libp2p_connection(data_dir=temp_dir_rel)
            cls.multiplexer = Multiplexer([cls.relay])
            cls.log_files.append(cls.relay.node.log_file)
            cls.multiplexer.connect()
            cls.multiplexers.append(cls.multiplexer)

            relay_peer = cls.relay.node.multiaddrs[0]

            temp_dir_1 = os.path.join(cls.t, "temp_dir_1")
            cls.connection1 = _make_libp2p_connection(
                data_dir=temp_dir_1,
                relay=False,
                entry_peers=[relay_peer],
            )
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            temp_dir_2 = os.path.join(cls.t, "temp_dir_2")
            cls.connection2 = _make_libp2p_connection(
                data_dir=temp_dir_2, entry_peers=[relay_peer]
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
            message=msg,
        )

        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
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
        assert (
            delivered_envelope.protocol_specification_id
            == original_envelope.protocol_specification_id
        )
        assert delivered_envelope.message != original_envelope.message
        assert original_envelope.message_bytes == delivered_envelope.message_bytes


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionRoutingRelayTwoDHTNodes(BaseP2PLibp2pTest):
    """Test that libp2p DHT network will reliably route envelopes from relay/non-relay to relay/non-relay nodes"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        def make_relay(directory, relay_peer):
            conn = _make_libp2p_connection(
                data_dir=directory,
                relay=False,
                entry_peers=[relay_peer],
            )
            mux = Multiplexer([conn])
            cls.connections.append(conn)
            cls.log_files.append(conn.node.log_file)
            mux.connect()
            cls.multiplexers.append(mux)

        try:
            temp_dir_rel_1 = os.path.join(cls.t, "temp_dir_rel_1")
            cls.connection_relay_1 = _make_libp2p_connection(data_dir=temp_dir_rel_1)
            cls.multiplexer_relay_1 = Multiplexer(
                [cls.connection_relay_1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_relay_1.node.log_file)
            cls.multiplexer_relay_1.connect()
            cls.multiplexers.append(cls.multiplexer_relay_1)

            relay_peer_1 = cls.connection_relay_1.node.multiaddrs[0]

            temp_dir_rel_2 = os.path.join(cls.t, "temp_dir_rel_2")
            cls.connection_relay_2 = _make_libp2p_connection(
                data_dir=temp_dir_rel_2, entry_peers=[relay_peer_1]
            )
            cls.multiplexer_relay_2 = Multiplexer(
                [cls.connection_relay_2], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_relay_2.node.log_file)
            cls.multiplexer_relay_2.connect()
            cls.multiplexers.append(cls.multiplexer_relay_2)

            relay_peer_2 = cls.connection_relay_2.node.multiaddrs[0]

            cls.connections = [cls.connection_relay_1, cls.connection_relay_2]

            for i in range(DEFAULT_NET_SIZE // 2 + 1):
                temp_dir_1 = os.path.join(cls.t, f"temp_dir_conn_{i}_1")
                temp_dir_2 = os.path.join(cls.t, f"temp_dir_conn_{i}_2")
                make_relay(temp_dir_1, relay_peer_1)
                make_relay(temp_dir_2, relay_peer_2)

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

        nodes = range(len(self.multiplexers))
        for u, v in permutations(nodes, 2):
            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )
            envelope = Envelope(
                to=addrs[v],
                sender=addrs[u],
                message=msg,
            )

            self.multiplexers[u].put(envelope)
            delivered_envelope = self.multiplexers[v].get(block=True, timeout=10)

            assert delivered_envelope is not None
            assert delivered_envelope.to == envelope.to
            assert delivered_envelope.sender == envelope.sender
            assert (
                delivered_envelope.protocol_specification_id
                == envelope.protocol_specification_id
            )
            assert delivered_envelope.message != envelope.message
            msg = DefaultMessage.serializer.decode(delivered_envelope.message)
            msg.sender = delivered_envelope.sender
            msg.to = delivered_envelope.to
            assert envelope.message == msg


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
        connection = _make_libp2p_connection(data_dir=self.tmp_dir)
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

    def _make_envelope(
        self,
        sender_address: str,
        receiver_address: str,
        message_id: int = 1,
        target: int = 0,
    ):
        """Make an envelope for testing purposes."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=message_id,
            target=target,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=receiver_address,
            sender=sender_address,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )
        return envelope

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        aea_ledger_fetchai = make_crypto(FetchAICrypto.identifier)
        aea_ledger_ethereum = make_crypto(EthereumCrypto.identifier)

        try:
            temp_dir_1 = os.path.join(cls.t, "temp_dir_1")
            cls.connection1 = _make_libp2p_connection(
                data_dir=temp_dir_1, agent_key=aea_ledger_fetchai
            )
            cls.multiplexer1 = Multiplexer(
                [cls.connection1], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            genesis_peer = cls.connection1.node.multiaddrs[0]

            temp_dir_2 = os.path.join(cls.t, "temp_dir_2")
            cls.connection2 = _make_libp2p_connection(
                data_dir=temp_dir_2,
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
        assert self.connection1.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed(self):
        """Test envelope routed."""
        addr_1 = self.connection2.node.address
        addr_2 = self.connection1.node.address

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
            message=msg,
        )

        # make the send to fail
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
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message != envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        msg.to = delivered_envelope.to
        msg.sender = delivered_envelope.sender
        assert envelope.message == msg


@libp2p_log_on_failure_all
class TestP2PLibp2PReceiveEnvelope(BaseTestP2PLibp2p):
    """Test that connection will receive envelope with error, and that reconnection fixes it."""

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
            message=msg,
        )

        # make the receive to fail
        with mock.patch.object(
            self.connection2.logger, "exception"
        ) as _mock_logger, mock.patch.object(
            self.connection2.node.pipe, "read", side_effect=Exception("some error")
        ):
            self.multiplexer1.put(envelope)
            delivered_envelope = self.multiplexer2.get(block=True, timeout=20)
            _mock_logger.assert_has_calls(
                [
                    call(
                        "Failed to read. Exception: some error. Try reconnect to node and read again."
                    )
                ]
            )

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message != envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)
        msg.to = delivered_envelope.to
        msg.sender = delivered_envelope.sender
        assert envelope.message == msg


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
        addr_1 = self.connection1.address
        addr_2 = self.connection2.address

        sent_envelopes = [
            self._make_envelope(addr_1, addr_2, i + 1, i)
            for i in range(self.NB_ENVELOPES)
        ]
        for envelope in sent_envelopes:
            self.multiplexer1.put(envelope)

        received_envelopes = []
        for _ in range(self.NB_ENVELOPES):
            envelope = self.multiplexer2.get(block=True, timeout=20)
            received_envelopes.append(envelope)

        # test no new message is "created"
        with pytest.raises(Empty):
            self.multiplexer2.get(block=True, timeout=1)

        assert len(sent_envelopes) == len(
            received_envelopes
        ), f"expected number of envelopes {len(sent_envelopes)}, got {len(received_envelopes)}"
        for expected, actual in zip(sent_envelopes, received_envelopes):
            assert expected.message == actual.message, (
                "message content differ; probably a wrong message "
                "ordering on the receiving end"
            )


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

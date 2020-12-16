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
"""This test module contains resilience and fault tolerance tests for P2PLibp2p connection."""
import os
import shutil
import tempfile
import time

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p.check_dependencies import build_node
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.default.serialization import DefaultSerializer

from tests.conftest import (
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestart:
    """Test that connection will reliably route envelope to destination in case of relay node restart within timeout"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        build_node(cls.t)
        cls.log_files = []
        cls.multiplexers = []

        try:
            cls.genesis = _make_libp2p_connection(
                DEFAULT_PORT + 1, build_directory=cls.t
            )

            cls.multiplexer_genesis = Multiplexer([cls.genesis])
            cls.multiplexer_genesis.connect()
            cls.log_files.append(cls.genesis.node.log_file)
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.genesis.node.multiaddrs[0]

            with open("node_key", "wb") as f:
                make_crypto(DEFAULT_LEDGER).dump(f)
                cls.relay_key_path = "node_key"

            cls.relay = _make_libp2p_connection(
                port=DEFAULT_PORT + 2,
                entry_peers=[genesis_peer],
                node_key_file=cls.relay_key_path,
                build_directory=cls.t,
            )
            cls.multiplexer_relay = Multiplexer([cls.relay])
            cls.multiplexer_relay.connect()
            cls.log_files.append(cls.relay.node.log_file)
            cls.multiplexers.append(cls.multiplexer_relay)

            relay_peer = cls.relay.node.multiaddrs[0]

            cls.connection = _make_libp2p_connection(
                DEFAULT_PORT + 3,
                relay=False,
                entry_peers=[relay_peer],
                build_directory=cls.t,
            )
            cls.multiplexer = Multiplexer([cls.connection])
            cls.multiplexer.connect()
            cls.log_files.append(cls.connection.node.log_file)
            cls.multiplexers.append(cls.multiplexer)
        except Exception:
            cls.teardown_class()
            raise

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.relay.is_connected is True
        assert self.connection.is_connected is True

    def test_envelope_routed_after_relay_restart(self):
        """Test envelope routed after relay restart."""
        addr_1 = self.connection.address
        addr_2 = self.genesis.address

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

        self.multiplexer.put(envelope)
        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer_relay.disconnect()

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"helloAfterRestart",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer.put(envelope)
        time.sleep(5)

        TestLibp2pConnectionRelayNodeRestart.relay = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            entry_peers=[self.genesis.node.multiaddrs[0]],
            node_key_file=self.relay_key_path,
            build_directory=self.t,
        )
        TestLibp2pConnectionRelayNodeRestart.multiplexer_relay = Multiplexer(
            [self.relay]
        )
        self.multiplexer_relay.connect()
        TestLibp2pConnectionRelayNodeRestart.multiplexers.append(self.multiplexer_relay)

        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message_bytes == envelope.message_bytes

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
class TestLibp2pConnectionAgentMobility:
    """Test that connection will correctly route envelope to destination that changed its peer"""

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
            cls.genesis = _make_libp2p_connection(DEFAULT_PORT)

            cls.multiplexer_genesis = Multiplexer([cls.genesis])
            cls.log_files.append(cls.genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.genesis.node.multiaddrs[0]

            cls.connection1 = _make_libp2p_connection(
                DEFAULT_PORT + 1, entry_peers=[genesis_peer]
            )
            cls.multiplexer1 = Multiplexer([cls.connection1])
            cls.log_files.append(cls.connection1.node.log_file)
            cls.multiplexer1.connect()
            cls.multiplexers.append(cls.multiplexer1)

            cls.connection2 = _make_libp2p_connection(
                DEFAULT_PORT + 2, entry_peers=[genesis_peer]
            )
            cls.multiplexer2 = Multiplexer([cls.connection2])
            cls.log_files.append(cls.connection2.node.log_file)
            cls.multiplexer2.connect()
            cls.multiplexers.append(cls.multiplexer2)

            cls.connection_addr = cls.connection2.address
        except Exception as e:
            cls.teardown_class()
            raise e

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.connection1.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed_after_peer_changed(self):
        """Test envelope routed after peer changed."""
        addr_1 = self.connection1.address
        addr_2 = self.connection2.address

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
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer2.disconnect()

        TestLibp2pConnectionAgentMobility.connection2 = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            entry_peers=[self.genesis.node.multiaddrs[0]],
            agent_address=self.connection_addr,
        )
        TestLibp2pConnectionAgentMobility.multiplexer2 = Multiplexer([self.connection2])
        self.multiplexer2.connect()
        TestLibp2pConnectionAgentMobility.multiplexers.append(self.multiplexer2)
        time.sleep(3)

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"helloAfterChangingPeer",
        )
        envelope = Envelope(
            to=addr_2, sender=addr_1, protocol_id=msg.protocol_id, message=msg.encode(),
        )

        self.multiplexer1.put(envelope)

        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message_bytes == envelope.message_bytes

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

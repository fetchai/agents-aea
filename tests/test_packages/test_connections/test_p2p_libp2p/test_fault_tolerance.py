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

import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p.check_dependencies import build_node
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.default.serialization import DefaultSerializer

from tests.common.utils import wait_for_condition
from tests.conftest import (
    MAX_FLAKY_RERUNS_INTEGRATION,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_INTEGRATION)
class BaseTestLibp2pRelay:
    """Base test class for libp2p connection relay."""

    @libp2p_log_on_failure
    def setup(self):
        """Set the test up"""
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        os.chdir(self.t)
        build_node(self.t)
        self.log_files = []
        self.multiplexers = []

    def change_state_and_wait(
        self,
        multiplexer: Multiplexer,
        expected_is_connected: bool = False,
        timeout: int = 10,
    ) -> None:
        """
        Change state of a multiplexer (either connect or disconnect) and wait.

        :param multiplexer: the multiplexer to connect/disconnect.
        :param expected_is_connected: whether it should be connected or disconnected.
        :param timeout: the maximum number seconds to wait.
        :return: None
        """
        wait_for_condition(
            lambda: multiplexer.is_connected == expected_is_connected, timeout=timeout
        )

    def teardown(self):
        """Tear down the test"""
        for mux in self.multiplexers:
            mux.disconnect()
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestartIncomingEnvelopes(BaseTestLibp2pRelay):
    """Test that connection will reliably receive envelopes after its relay node restarted"""

    @libp2p_log_on_failure
    def setup(self):
        """Set the test up"""
        super().setup()
        temp_dir_gen = os.path.join(self.t, "temp_dir_gen")
        os.mkdir(temp_dir_gen)
        self.genesis = _make_libp2p_connection(
            data_dir=temp_dir_gen, port=DEFAULT_PORT + 1, build_directory=self.t
        )

        self.multiplexer_genesis = Multiplexer(
            [self.genesis], protocols=[DefaultMessage]
        )
        self.multiplexer_genesis.connect()
        self.log_files.append(self.genesis.node.log_file)
        self.multiplexers.append(self.multiplexer_genesis)

        genesis_peer = self.genesis.node.multiaddrs[0]

        file = "node_key"
        make_crypto(DEFAULT_LEDGER).dump(file)
        self.relay_key_path = file

        temp_dir_rel = os.path.join(self.t, "temp_dir_rel")
        os.mkdir(temp_dir_rel)
        self.relay = _make_libp2p_connection(
            data_dir=temp_dir_rel,
            port=DEFAULT_PORT + 2,
            entry_peers=[genesis_peer],
            node_key_file=self.relay_key_path,
            build_directory=self.t,
        )
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.log_files.append(self.relay.node.log_file)
        self.multiplexers.append(self.multiplexer_relay)

        relay_peer = self.relay.node.multiaddrs[0]

        temp_dir_1 = os.path.join(self.t, "temp_dir_1")
        os.mkdir(temp_dir_1)
        self.connection = _make_libp2p_connection(
            data_dir=temp_dir_1,
            port=DEFAULT_PORT + 3,
            relay=False,
            entry_peers=[relay_peer],
            build_directory=self.t,
        )
        self.multiplexer = Multiplexer([self.connection], protocols=[DefaultMessage])
        self.multiplexer.connect()
        self.log_files.append(self.connection.node.log_file)
        self.multiplexers.append(self.multiplexer)

        temp_dir_2 = os.path.join(self.t, "temp_dir_2")
        os.mkdir(temp_dir_2)
        self.connection2 = _make_libp2p_connection(
            data_dir=temp_dir_2,
            port=DEFAULT_PORT + 4,
            relay=False,
            entry_peers=[relay_peer],
            build_directory=self.t,
        )
        self.multiplexer2 = Multiplexer([self.connection2], protocols=[DefaultMessage])
        self.multiplexer2.connect()
        self.log_files.append(self.connection2.node.log_file)
        self.multiplexers.append(self.multiplexer2)

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.relay.is_connected is True
        assert self.connection.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed_from_peer_after_relay_restart(self):
        """Test envelope routed from third peer after relay restart."""
        addr_1 = self.genesis.address
        addr_2 = self.connection.address

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
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer_genesis.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

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
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        time.sleep(10)
        self.multiplexer_genesis.put(envelope)

        delivered_envelope = self.multiplexer.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes

    def test_envelope_routed_from_client_after_relay_restart(self):
        """Test envelope routed from third relay client after relay restart."""
        addr_1 = self.connection.address
        addr_2 = self.connection2.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=addr_1,
            sender=addr_2,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer2.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"helloAfterRestart",
        )

        envelope = Envelope(
            to=addr_1,
            sender=addr_2,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        time.sleep(10)
        self.multiplexer2.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestartOutgoingEnvelopes(BaseTestLibp2pRelay):
    """Test that connection will reliably route envelope to destination in case of relay node restart within timeout"""

    @libp2p_log_on_failure
    def setup(self):
        """Set the test up"""
        super().setup()
        temp_dir_gen = os.path.join(self.t, "temp_dir_gen")
        os.mkdir(temp_dir_gen)
        self.genesis = _make_libp2p_connection(
            data_dir=temp_dir_gen, port=DEFAULT_PORT + 1, build_directory=self.t
        )

        self.multiplexer_genesis = Multiplexer(
            [self.genesis], protocols=[DefaultMessage]
        )
        self.multiplexer_genesis.connect()
        self.log_files.append(self.genesis.node.log_file)
        self.multiplexers.append(self.multiplexer_genesis)

        genesis_peer = self.genesis.node.multiaddrs[0]

        file = "node_key"
        make_crypto(DEFAULT_LEDGER).dump(file)
        self.relay_key_path = file

        temp_dir_rel = os.path.join(self.t, "temp_dir_rel")
        os.mkdir(temp_dir_rel)
        self.relay = _make_libp2p_connection(
            data_dir=temp_dir_rel,
            port=DEFAULT_PORT + 2,
            entry_peers=[genesis_peer],
            node_key_file=self.relay_key_path,
            build_directory=self.t,
        )
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.log_files.append(self.relay.node.log_file)
        self.multiplexers.append(self.multiplexer_relay)

        relay_peer = self.relay.node.multiaddrs[0]

        temp_dir_1 = os.path.join(self.t, "temp_dir_1")
        os.mkdir(temp_dir_1)
        self.connection = _make_libp2p_connection(
            data_dir=temp_dir_1,
            port=DEFAULT_PORT + 3,
            relay=False,
            entry_peers=[relay_peer],
            build_directory=self.t,
        )
        self.multiplexer = Multiplexer([self.connection], protocols=[DefaultMessage])
        self.multiplexer.connect()
        self.log_files.append(self.connection.node.log_file)
        self.multiplexers.append(self.multiplexer)

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
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer.put(envelope)
        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

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
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
        )

        time.sleep(10)
        self.multiplexer.put(envelope)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes


@libp2p_log_on_failure_all
class TestLibp2pConnectionAgentMobility(BaseTestLibp2pRelay):
    """Test that connection will correctly route envelope to destination that changed its peer"""

    @libp2p_log_on_failure
    def setup(self):
        """Set the test up"""
        super().setup()
        temp_dir_gen = os.path.join(self.t, "temp_dir_gen")
        os.mkdir(temp_dir_gen)
        self.genesis = _make_libp2p_connection(data_dir=temp_dir_gen, port=DEFAULT_PORT)

        self.multiplexer_genesis = Multiplexer(
            [self.genesis], protocols=[DefaultMessage]
        )
        self.log_files.append(self.genesis.node.log_file)
        self.multiplexer_genesis.connect()
        self.multiplexers.append(self.multiplexer_genesis)

        genesis_peer = self.genesis.node.multiaddrs[0]

        temp_dir_1 = os.path.join(self.t, "temp_dir_1")
        os.mkdir(temp_dir_1)
        self.connection1 = _make_libp2p_connection(
            data_dir=temp_dir_1, port=DEFAULT_PORT + 1, entry_peers=[genesis_peer]
        )
        self.multiplexer1 = Multiplexer([self.connection1], protocols=[DefaultMessage])
        self.log_files.append(self.connection1.node.log_file)
        self.multiplexer1.connect()
        self.multiplexers.append(self.multiplexer1)

        self.connection_key = make_crypto(DEFAULT_LEDGER)
        temp_dir_2 = os.path.join(self.t, "temp_dir_2")
        os.mkdir(temp_dir_2)
        self.connection2 = _make_libp2p_connection(
            data_dir=temp_dir_2,
            port=DEFAULT_PORT + 2,
            entry_peers=[genesis_peer],
            agent_key=self.connection_key,
        )
        self.multiplexer2 = Multiplexer([self.connection2], protocols=[DefaultMessage])
        self.log_files.append(self.connection2.node.log_file)
        self.multiplexer2.connect()
        self.multiplexers.append(self.multiplexer2)

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
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(msg),
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
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer2.disconnect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer2 = Multiplexer([self.connection2], protocols=[DefaultMessage])
        self.multiplexer2.connect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer2)

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"helloAfterChangingPeer",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_specification_id=msg.protocol_specification_id,
            message=msg.encode(),
        )

        time.sleep(10)
        self.multiplexer1.put(envelope)

        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message_bytes == envelope.message_bytes

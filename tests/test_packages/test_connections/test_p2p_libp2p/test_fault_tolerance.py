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
"""This test module contains resilience and fault tolerance tests for P2PLibp2p connection."""

import time

import pytest

from aea.crypto.registries import make_crypto
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.valory.connections.p2p_libp2p.check_dependencies import build_node

from tests.common.utils import wait_for_condition
from tests.conftest import MAX_FLAKY_RERUNS_INTEGRATION
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
)


TIMEOUT = 20


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_INTEGRATION)
class BaseTestLibp2pRelay(BaseP2PLibp2pTest):
    """Base test class for libp2p connection relay."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()
        build_node(cls.t)

    def change_state_and_wait(
        self,
        multiplexer: Multiplexer,
        expected_is_connected: bool = False,
        timeout: int = TIMEOUT,
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


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestartIncomingEnvelopes(BaseTestLibp2pRelay):
    """Test that connection will reliably receive envelopes after its relay node restarted"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()
        cls.genesis = _make_libp2p_connection()

        cls.multiplexer_genesis = Multiplexer([cls.genesis], protocols=[DefaultMessage])
        cls.multiplexer_genesis.connect()
        cls.log_files.append(cls.genesis.node.log_file)
        cls.multiplexers.append(cls.multiplexer_genesis)

        genesis_peer = cls.genesis.node.multiaddrs[0]

        cls.relay = _make_libp2p_connection(entry_peers=[genesis_peer])
        cls.multiplexer_relay = Multiplexer([cls.relay], protocols=[DefaultMessage])
        cls.multiplexer_relay.connect()
        cls.log_files.append(cls.relay.node.log_file)
        cls.multiplexers.append(cls.multiplexer_relay)

        relay_peer = cls.relay.node.multiaddrs[0]

        cls.connection = _make_libp2p_connection(relay=False, entry_peers=[relay_peer])
        cls.multiplexer = Multiplexer([cls.connection], protocols=[DefaultMessage])
        cls.multiplexer.connect()
        cls.log_files.append(cls.connection.node.log_file)
        cls.multiplexers.append(cls.multiplexer)

        cls.connection2 = _make_libp2p_connection(relay=False, entry_peers=[relay_peer])
        cls.multiplexer2 = Multiplexer([cls.connection2], protocols=[DefaultMessage])
        cls.multiplexer2.connect()
        cls.log_files.append(cls.connection2.node.log_file)
        cls.multiplexers.append(cls.multiplexer2)

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.relay.is_connected is True
        assert self.connection.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed_from_peer_after_relay_restart(self):
        """Test envelope routed from third peer after relay restart."""

        sender = self.genesis.address
        to = self.connection.address

        envelope = self.enveloped_default_message(to=to, sender=sender)
        self.multiplexer_genesis.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

        envelope = self.enveloped_default_message(to=to, sender=sender)
        time.sleep(10)
        self.multiplexer_genesis.put(envelope)

        delivered_envelope = self.multiplexer.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    def test_envelope_routed_from_client_after_relay_restart(self):
        """Test envelope routed from third relay client after relay restart."""

        to = self.connection.address
        sender = self.connection2.address

        envelope = self.enveloped_default_message(to=to, sender=sender)
        self.multiplexer2.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

        envelope = self.enveloped_default_message(to=to, sender=sender)
        time.sleep(10)
        self.multiplexer2.put(envelope)
        delivered_envelope = self.multiplexer.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestartOutgoingEnvelopes(BaseTestLibp2pRelay):
    """Test that connection will reliably route envelope to destination in case of relay node restart within timeout"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.genesis = _make_libp2p_connection()
        cls.multiplexer_genesis = Multiplexer([cls.genesis], protocols=[DefaultMessage])
        cls.multiplexer_genesis.connect()
        cls.log_files.append(cls.genesis.node.log_file)
        cls.multiplexers.append(cls.multiplexer_genesis)

        genesis_peer = cls.genesis.node.multiaddrs[0]
        cls.relay = _make_libp2p_connection(entry_peers=[genesis_peer])
        cls.multiplexer_relay = Multiplexer([cls.relay], protocols=[DefaultMessage])
        cls.multiplexer_relay.connect()
        cls.log_files.append(cls.relay.node.log_file)
        cls.multiplexers.append(cls.multiplexer_relay)

        relay_peer = cls.relay.node.multiaddrs[0]
        cls.connection = _make_libp2p_connection(relay=False, entry_peers=[relay_peer])
        cls.multiplexer = Multiplexer([cls.connection], protocols=[DefaultMessage])
        cls.multiplexer.connect()
        cls.log_files.append(cls.connection.node.log_file)
        cls.multiplexers.append(cls.multiplexer)

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.relay.is_connected is True
        assert self.connection.is_connected is True

    def test_envelope_routed_after_relay_restart(self):
        """Test envelope routed after relay restart."""
        sender = self.connection.address
        to = self.genesis.address

        envelope = self.enveloped_default_message(to=to, sender=sender)

        self.multiplexer.put(envelope)
        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)

        envelope = self.enveloped_default_message(to=to, sender=sender)
        time.sleep(10)
        self.multiplexer.put(envelope)

        # currently, multiplexer cannot be restarted
        self.multiplexer_relay = Multiplexer([self.relay], protocols=[DefaultMessage])
        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer_relay)

        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=TIMEOUT)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@libp2p_log_on_failure_all
class TestLibp2pConnectionAgentMobility(BaseTestLibp2pRelay):
    """Test that connection will correctly route envelope to destination that changed its peer"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.genesis = _make_libp2p_connection()
        cls.multiplexer_genesis = Multiplexer([cls.genesis], protocols=[DefaultMessage])
        cls.log_files.append(cls.genesis.node.log_file)
        cls.multiplexer_genesis.connect()
        cls.multiplexers.append(cls.multiplexer_genesis)

        genesis_peer = cls.genesis.node.multiaddrs[0]
        cls.connection1 = _make_libp2p_connection(entry_peers=[genesis_peer])
        cls.multiplexer1 = Multiplexer([cls.connection1], protocols=[DefaultMessage])
        cls.log_files.append(cls.connection1.node.log_file)
        cls.multiplexer1.connect()
        cls.multiplexers.append(cls.multiplexer1)

        cls.connection_key = make_crypto("fetchai")
        cls.connection2 = _make_libp2p_connection(
            entry_peers=[genesis_peer],
            agent_key=cls.connection_key,
        )
        cls.multiplexer2 = Multiplexer([cls.connection2], protocols=[DefaultMessage])
        cls.log_files.append(cls.connection2.node.log_file)
        cls.multiplexer2.connect()
        cls.multiplexers.append(cls.multiplexer2)

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.connection1.is_connected is True
        assert self.connection2.is_connected is True

    def test_envelope_routed_after_peer_changed(self):
        """Test envelope routed after peer changed."""
        sender = self.connection1.address
        to = self.connection2.address

        envelope = self.enveloped_default_message(to=to, sender=sender)
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        self.multiplexer2.disconnect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=False)

        # currently, multiplexer cannot be restarted
        self.multiplexer2 = Multiplexer([self.connection2], protocols=[DefaultMessage])
        self.multiplexer2.connect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=True)
        self.multiplexers.append(self.multiplexer2)

        envelope = self.enveloped_default_message(to=to, sender=sender)
        time.sleep(10)
        self.multiplexer1.put(envelope)
        delivered_envelope = self.multiplexer2.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

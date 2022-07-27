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

import pytest

from aea.multiplexer import Empty, Multiplexer

from packages.valory.connections.p2p_libp2p.check_dependencies import build_node

from tests.common.utils import wait_for_condition
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    libp2p_log_on_failure_all,
)


TIMEOUT = 10


class BaseTestLibp2pRelay(BaseP2PLibp2pTest):
    """Base test class for libp2p connection relay."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()
        build_node(cls.tmp)

    def change_state_and_wait(
        self,
        multiplexer: Multiplexer,
        expected_is_connected: bool = False,
        timeout: int = TIMEOUT,
    ) -> None:
        """Change state of a multiplexer (either connect or disconnect) and wait."""
        wait_for_condition(
            lambda: multiplexer.is_connected == expected_is_connected, timeout=timeout
        )


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestart(BaseTestLibp2pRelay):
    """Test that connection will reliably forward envelopes after its relay node restarted"""

    def setup(self):
        """Set up the individual test method"""

        self.genesis = self.make_connection()
        genesis_peer = self.genesis.node.multiaddrs[0]
        self.relay = self.make_connection(entry_peers=[genesis_peer])
        relay_peer = self.relay.node.multiaddrs[0]
        self.connection1 = self.make_connection(relay=False, entry_peers=[relay_peer])
        self.connection2 = self.make_connection(relay=False, entry_peers=[relay_peer])

        # create references for disconnecting and reconnecting
        self.multiplexer_genesis = self.multiplexers[0]
        self.multiplexer_relay = self.multiplexers[1]
        self.multiplexer1 = self.multiplexers[2]
        self.multiplexer2 = self.multiplexers[3]

    def teardown(self):
        """Teardown"""
        self._disconnect()
        self.multiplexers.clear()

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_envelope_routed_from_peer_after_relay_restart(self):
        """Test envelope routed from third peer after relay restart."""

        to = self.connection1.address
        sender = self.genesis.address

        def attempt_sending():
            envelope = self.enveloped_default_message(to=to, sender=sender)
            self.multiplexer_genesis.put(envelope)
            delivered_envelope = self.multiplexer1.get(block=True, timeout=TIMEOUT)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        assert self.multiplexer_relay.is_connected
        attempt_sending()

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)
        assert not self.multiplexer_relay.is_connected

        with pytest.raises(Empty):
            attempt_sending()

        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        assert self.multiplexer_relay.is_connected
        attempt_sending()

    def test_envelope_routed_from_client_after_relay_restart(self):
        """Test envelope routed from third relay client after relay restart."""

        to = self.connection1.address
        sender = self.connection2.address

        def attempt_sending():
            envelope = self.enveloped_default_message(to=to, sender=sender)
            self.multiplexer2.put(envelope)
            delivered_envelope = self.multiplexer1.get(block=True, timeout=TIMEOUT)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        assert self.multiplexer_relay.is_connected
        attempt_sending()

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)
        assert not self.multiplexer_relay.is_connected

        with pytest.raises(Empty):
            attempt_sending()

        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        assert self.multiplexer_relay.is_connected
        attempt_sending()

    def test_envelope_routed_after_relay_restart(self):
        """Test envelope routed after relay restart."""

        sender = self.connection1.address
        to = self.genesis.address

        def attempt_sending():
            envelope = self.enveloped_default_message(to=to, sender=sender)
            self.multiplexer1.put(envelope)
            delivered_envelope = self.multiplexer_genesis.get(
                block=True, timeout=TIMEOUT
            )
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        assert self.multiplexer_relay.is_connected
        attempt_sending()

        self.multiplexer_relay.disconnect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=False)
        assert not self.multiplexer_relay.is_connected

        with pytest.raises(Empty):
            attempt_sending()

        self.multiplexer_relay.connect()
        self.change_state_and_wait(self.multiplexer_relay, expected_is_connected=True)
        assert self.multiplexer_relay.is_connected
        attempt_sending()


@libp2p_log_on_failure_all
class TestLibp2pConnectionAgentMobility(BaseTestLibp2pRelay):
    """Test that connection will correctly route envelope to destination that changed its peer"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        cls.genesis = cls.make_connection()
        genesis_peer = cls.genesis.node.multiaddrs[0]
        cls.connection1 = cls.make_connection(entry_peers=[genesis_peer])
        cls.connection2 = cls.make_connection(
            entry_peers=[genesis_peer],
            agent_key=cls.default_crypto,
        )

        cls.multiplexer_genesis = cls.multiplexers[0]
        cls.multiplexer1 = cls.multiplexers[1]
        cls.multiplexer2 = cls.multiplexers[2]

    def test_envelope_routed_after_peer_changed(self):
        """Test envelope routed after peer changed."""

        sender = self.connection1.address
        to = self.connection2.address

        def attempt_sending():
            envelope = self.enveloped_default_message(to=to, sender=sender)
            self.multiplexer1.put(envelope)
            delivered_envelope = self.multiplexer2.get(block=True, timeout=TIMEOUT)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

        assert self.multiplexer2.is_connected
        attempt_sending()

        self.multiplexer2.disconnect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=False)
        assert not self.multiplexer2.is_connected

        with pytest.raises(Empty):
            attempt_sending()

        self.multiplexer2.connect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=True)

        self.multiplexer2.connect()
        self.change_state_and_wait(self.multiplexer2, expected_is_connected=True)
        assert self.multiplexer2.is_connected
        attempt_sending()

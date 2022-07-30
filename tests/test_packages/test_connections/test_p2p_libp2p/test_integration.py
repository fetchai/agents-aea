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

import itertools

import pytest

from aea.helpers.acn.uri import Uri

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    libp2p_log_on_failure_all,
)


DEFAULT_NET_SIZE = 4


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionIntegrationTest(BaseP2PLibp2pTest):
    """Test mix of relay/delegate agents and client connections work together"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        # relays
        main_relay = cls.make_connection()
        main_relay_peer = main_relay.node.multiaddrs[0]
        relay_2 = cls.make_connection(entry_peers=[main_relay_peer])
        relay_peer_2 = relay_2.node.multiaddrs[0]

        # delegates
        delegate_1 = cls.make_connection(
            entry_peers=[main_relay_peer], delegate=True, mailbox=True
        )
        delegate_2 = cls.make_connection(
            entry_peers=[relay_peer_2], delegate=True, mailbox=True
        )

        # agents
        cls.make_connection(entry_peers=[main_relay_peer], relay=False)
        cls.make_connection(entry_peers=[relay_peer_2], relay=False)

        # clients
        cls.make_client_connection(
            peer_public_key=delegate_1.node.pub,
            node_host=delegate_1.node.delegate_uri.host,
            node_port=delegate_1.node.delegate_uri.port,
        )
        cls.make_client_connection(
            peer_public_key=delegate_2.node.pub,
            node_host=delegate_2.node.delegate_uri.host,
            node_port=delegate_2.node.delegate_uri.port,
        )

        # mailboxes
        cls.make_mailbox_connection(
            peer_public_key=delegate_1.node.pub,
            node_host=Uri(delegate_1.node.mailbox_uri).host,
            node_port=Uri(delegate_1.node.mailbox_uri).port,
        )
        cls.make_mailbox_connection(
            peer_public_key=delegate_2.node.pub,
            node_host=Uri(delegate_2.node.mailbox_uri).host,
            node_port=Uri(delegate_2.node.mailbox_uri).port,
        )

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_connected

    def test_send_and_receive(self):
        """Test envelope send/received by every pair of connection."""

        for sending, receiving in itertools.permutations(self.multiplexers, 2):

            sender = next(c.address for c in sending.connections)
            to = next(c.address for c in receiving.connections)
            envelope = self.enveloped_default_message(to=to, sender=sender)

            sending.put(envelope)
            delivered_envelope = receiving.get(block=True, timeout=10)
            assert delivered_envelope is not None
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

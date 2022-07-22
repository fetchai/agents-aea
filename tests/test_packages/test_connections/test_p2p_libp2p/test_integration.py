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
from copy import copy
from unittest.mock import Mock

import pytest

from aea.helpers.acn.uri import Uri
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    _make_libp2p_connection,
    _make_libp2p_client_connection,
    _make_libp2p_mailbox_connection,
    libp2p_log_on_failure_all,
)


DEFAULT_NET_SIZE = 4

MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionIntegrationTest(BaseP2PLibp2pTest):
    """Test mix of relay/delegate agents and client connections work together"""

    @classmethod
    def _multiplex_it(cls, conn):
        multiplexer = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])
        cls.multiplexers.append(multiplexer)
        multiplexer.connect()

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        # relays
        main_relay = _make_libp2p_connection(relay=True)
        cls.log_files.append(main_relay.node.log_file)
        cls._multiplex_it(main_relay)
        main_relay_peer = main_relay.node.multiaddrs[0]

        relay_2 = _make_libp2p_connection(entry_peers=[main_relay_peer], relay=True)
        cls.log_files.append(relay_2.node.log_file)
        cls._multiplex_it(relay_2)
        relay_peer_2 = relay_2.node.multiaddrs[0]

        # delegates
        delegate_1 = _make_libp2p_connection(
            entry_peers=[main_relay_peer],
            relay=True,
            delegate=True,
            mailbox=True,
        )
        cls.log_files.append(delegate_1.node.log_file)
        cls._multiplex_it(delegate_1)

        delegate_2 = _make_libp2p_connection(
            entry_peers=[relay_peer_2],
            relay=True,
            delegate=True,
            mailbox=True,
        )
        cls.log_files.append(delegate_2.node.log_file)
        cls._multiplex_it(delegate_2)

        # agents
        agent_connection_1 = _make_libp2p_connection(
            entry_peers=[main_relay_peer],
            relay=False,
            delegate=False,
        )
        cls.log_files.append(agent_connection_1.node.log_file)
        cls._multiplex_it(agent_connection_1)

        agent_connection_2 = _make_libp2p_connection(
            entry_peers=[relay_peer_2],
            relay=False,
            delegate=False,
        )
        cls.log_files.append(agent_connection_2.node.log_file)
        cls._multiplex_it(agent_connection_2)

        # clients
        client_connection_1 = _make_libp2p_client_connection(
            peer_public_key=delegate_1.node.pub,
            **cls.get_delegate_host_port(delegate_1.node.delegate_uri),
        )
        cls._multiplex_it(client_connection_1)

        client_connection_2 = _make_libp2p_client_connection(
            peer_public_key=delegate_2.node.pub,
            **cls.get_delegate_host_port(delegate_2.node.delegate_uri),
        )
        cls._multiplex_it(client_connection_2)

        # mailboxes
        mailbox_connection_1 = _make_libp2p_mailbox_connection(
            peer_public_key=delegate_1.node.pub,
            **cls.get_delegate_host_port(Uri(delegate_1.node.mailbox_uri)),
        )
        cls._multiplex_it(mailbox_connection_1)

        mailbox_connection_2 = _make_libp2p_mailbox_connection(
            peer_public_key=delegate_2.node.pub,
            **cls.get_delegate_host_port(Uri(delegate_2.node.mailbox_uri)),
        )
        cls._multiplex_it(mailbox_connection_2)

    @classmethod
    def get_delegate_host_port(cls, delegate_uri: Uri) -> dict:
        """Get delegate/mailbox server config dict."""
        return {"node_port": delegate_uri.port, "node_host": delegate_uri.host}

    def test_connection_is_established(self):
        """Test connection established."""
        assert self.all_multiplexer_connections_connected

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

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
"""This test module contains tests for P2PLibp2p connection."""
import itertools
import os
import shutil
import tempfile
from copy import copy
from unittest.mock import Mock

from aea.helpers.acn.uri import Uri
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import (
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    _make_libp2p_mailbox_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234
DEFAULT_NET_SIZE = 4

MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionIntegrationTest:
    """Test mix of relay/delegate agents and client connections work together"""

    BASE_PORT_NUM: int = DEFAULT_PORT

    @classmethod
    def get_port(cls) -> int:
        """Get next port to use for libp2p."""
        cls.BASE_PORT_NUM += 1
        return cls.BASE_PORT_NUM

    @classmethod
    def make_connection(cls, name, **kwargs):
        """Make a p2p connection."""
        if name in cls.multiplexers_dict:
            raise ValueError(f"Connection with name `{name}` already added")
        temp_dir = os.path.join(cls.t, name)
        os.mkdir(temp_dir)
        conn_options = copy(kwargs)
        conn_options["port"] = conn_options.get("port", cls.get_port())
        conn_options["data_dir"] = conn_options.get("data_dir", temp_dir)
        conn = _make_libp2p_connection(**conn_options)
        multiplexer = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])
        cls.log_files.append(conn.node.log_file)
        multiplexer.connect()
        cls.multiplexers_dict[name] = multiplexer
        cls.connections_dict[name] = conn
        return conn

    @classmethod
    def make_client_connection(cls, name, **kwargs):
        """Make a p2p client connection."""
        if name in cls.multiplexers_dict:
            raise ValueError(f"Connection with name `{name}` already added")
        temp_dir = os.path.join(cls.t, name)
        os.mkdir(temp_dir)
        conn_options = copy(kwargs)

        conn_options["data_dir"] = conn_options.get("data_dir", temp_dir)
        conn = _make_libp2p_client_connection(**conn_options)
        multiplexer = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])
        multiplexer.connect()
        cls.multiplexers_dict[name] = multiplexer
        cls.connections_dict[name] = conn
        return conn

    @classmethod
    def make_mailbox_connection(cls, name, **kwargs):
        """Make a p2p mailbox connection."""
        if name in cls.multiplexers_dict:
            raise ValueError(f"Connection with name `{name}` already added")
        temp_dir = os.path.join(cls.t, name)
        os.mkdir(temp_dir)
        conn_options = copy(kwargs)

        conn_options["data_dir"] = conn_options.get("data_dir", temp_dir)
        conn = _make_libp2p_mailbox_connection(**conn_options)
        multiplexer = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])
        multiplexer.connect()
        cls.multiplexers_dict[name] = multiplexer
        cls.connections_dict[name] = conn
        return conn

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []
        cls.multiplexers_dict = {}
        cls.connections_dict = {}
        cls.multiplexers = []

        try:
            cls.main_relay = cls.make_connection("main_relay", relay=True)
            main_relay = cls.main_relay.node.multiaddrs[0]
            cls.relay_2 = cls.make_connection(
                "relay_2", entry_peers=[main_relay], relay=True
            )
            relay_peer_2 = cls.relay_2.node.multiaddrs[0]

            cls.delegate_1 = cls.make_connection(
                "delegate_1",
                entry_peers=[main_relay],
                relay=True,
                delegate=True,
                delegate_port=cls.get_port(),
                mailbox_port=cls.get_port(),
                mailbox=True,
            )

            cls.delegate_2 = cls.make_connection(
                "delegate_2",
                entry_peers=[relay_peer_2],
                relay=True,
                delegate=True,
                delegate_port=cls.get_port(),
                mailbox_port=cls.get_port(),
                mailbox=True,
            )

            cls.agent_connection_1 = cls.make_connection(
                "agent_connection_1",
                entry_peers=[main_relay],
                relay=False,
                delegate=False,
            )

            cls.agent_connection_2 = cls.make_connection(
                "agent_connection_2",
                entry_peers=[relay_peer_2],
                relay=False,
                delegate=False,
            )
            cls.client_connection_1 = cls.make_client_connection(
                "client_1",
                peer_public_key=cls.delegate_1.node.pub,
                **cls.get_delegate_host_port(cls.delegate_1.node.delegate_uri),
            )

            cls.client_connection_2 = cls.make_client_connection(
                "client_2",
                peer_public_key=cls.delegate_2.node.pub,
                **cls.get_delegate_host_port(cls.delegate_2.node.delegate_uri),
            )
            cls.mailbox_connection_1 = cls.make_mailbox_connection(
                "mailbox_1",
                peer_public_key=cls.delegate_1.node.pub,
                **cls.get_delegate_host_port(Uri(cls.delegate_1.node.mailbox_uri)),
            )

            cls.mailbox_connection_2 = cls.make_mailbox_connection(
                "mailbox_2",
                peer_public_key=cls.delegate_2.node.pub,
                **cls.get_delegate_host_port(Uri(cls.delegate_2.node.mailbox_uri)),
            )
        except Exception:
            cls.teardown_class()
            raise

    @classmethod
    def get_delegate_host_port(cls, delegate_uri: Uri) -> dict:
        """Get delegate/mailbox server config dict."""
        return {"node_port": delegate_uri.port, "node_host": delegate_uri.host}

    def test_connection_is_established(self):
        """Test connection established."""
        for conn in self.connections_dict.values():
            assert conn.is_connected is True

    def send_message(self, from_name: str, to_name: str) -> None:
        """Send message from one connection to another and check it's delivered."""
        from_addr = self.connections_dict[from_name].address  # type: ignore
        to_addr = self.connections_dict[to_name].address  # type: ignore

        from_multiplexer = self.multiplexers_dict[from_name]  # type: ignore
        to_multiplexer = self.multiplexers_dict[to_name]  # type: ignore

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(to=to_addr, sender=from_addr, message=msg,)

        from_multiplexer.put(envelope)

        delivered_envelope = to_multiplexer.get(block=True, timeout=10)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert (
            delivered_envelope.protocol_specification_id
            == envelope.protocol_specification_id
        )
        assert delivered_envelope.message != envelope.message
        msg = DefaultMessage.serializer.decode(delivered_envelope.message)  # type: ignore
        msg.sender = delivered_envelope.sender
        msg.to = delivered_envelope.to
        assert envelope.message == msg

    def test_send_and_receive(self):
        """Test envelope send/received by every pair of connection."""
        for from_name, to_name in itertools.permutations(
            [
                "client_1",
                "client_2",
                "agent_connection_1",
                "agent_connection_2",
                "mailbox_1",
                "mailbox_2",
            ],
            2,
        ):
            self.send_message(from_name, to_name)

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()

        for mux in cls.multiplexers_dict.values():
            mux.disconnect()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

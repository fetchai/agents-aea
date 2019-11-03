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

"""This module contains the tests for the TCP connection communication."""
from aea.connections.tcp.tcp_client import TCPClientConnection
from aea.connections.tcp.tcp_server import TCPServerConnection
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer


class TestTCPCommunication:
    """Test that TCP Server and TCP Client can communicate."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.host = "127.0.0.1"
        cls.port = 8082

        cls.server_pbk = "server_pbk"
        cls.client_pbk_1 = "client_pbk_1"
        cls.client_pbk_2 = "client_pbk_2"
        cls.server_conn = TCPServerConnection(cls.server_pbk, cls.host, cls.port)
        cls.client_conn_1 = TCPClientConnection(cls.client_pbk_1, cls.host, cls.port)
        cls.client_conn_2 = TCPClientConnection(cls.client_pbk_2, cls.host, cls.port)

        cls.server_mailbox = MailBox(cls.server_conn)
        cls.client_1_mailbox = MailBox(cls.client_conn_1)
        cls.client_2_mailbox = MailBox(cls.client_conn_2)

        cls.server_mailbox.connect()
        cls.client_1_mailbox.connect()
        cls.client_2_mailbox.connect()

    def test_communication_client_server(self):
        """Test that envelopes can be sent from a client to a server."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg_bytes = DefaultSerializer().encode(msg)
        expected_envelope = Envelope(to=self.server_pbk, sender=self.client_pbk_1, protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
        self.client_1_mailbox.outbox.put(expected_envelope)
        actual_envelope = self.server_mailbox.inbox.get(block=True, timeout=5.0)

        assert expected_envelope == actual_envelope

    def test_communication_server_client(self):
        """Test that envelopes can be sent from a server to a client."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg_bytes = DefaultSerializer().encode(msg)

        expected_envelope = Envelope(to=self.client_pbk_1, sender=self.server_pbk, protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
        self.server_mailbox.outbox.put(expected_envelope)
        actual_envelope = self.client_1_mailbox.inbox.get(block=True, timeout=5.0)

        assert expected_envelope == actual_envelope

        expected_envelope = Envelope(to=self.client_pbk_2, sender=self.server_pbk, protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
        self.server_mailbox.outbox.put(expected_envelope)
        actual_envelope = self.client_2_mailbox.inbox.get(block=True, timeout=5.0)

        assert expected_envelope == actual_envelope

    @classmethod
    def teardown_class(cls):
        """Tear down the test class."""
        cls.server_mailbox.disconnect()
        cls.client_1_mailbox.disconnect()
        cls.client_2_mailbox.disconnect()

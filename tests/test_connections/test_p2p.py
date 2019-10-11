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

"""This module contains the tests of the P2P channel."""
import logging
import shutil
from pathlib import Path

from aea.connections.p2p.tcp_client import TCPClientChannel, TCPClientConnection
from aea.connections.p2p.tcp_server import TCPServerConnection, TCPServerChannel
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer


class TestTCP:
    """Test TCP connections."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        p = Path("/tmp/aea/test_tcp/")
        shutil.rmtree(str(p))
        p.mkdir(parents=True)

        socket_path = str(Path(p, "test_socket"))
        cls.server_pbk, cls.client_pbk = "server_pbk", "client_pbk"
        server_conn = TCPServerConnection(cls.server_pbk, TCPServerChannel(cls.server_pbk, socket_path, unix=True))
        client_conn = TCPClientConnection(cls.client_pbk, TCPClientChannel(cls.client_pbk, socket_path, unix=True))

        cls.server_mailbox = MailBox(server_conn)
        cls.client_mailbox = MailBox(client_conn)

        cls.server_mailbox.connect()
        cls.client_mailbox.connect()

    def test_communication(self):
        """Test that we are able to send an envelope from client to server."""
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello server")
        expected_envelope = Envelope(to=self.server_pbk, sender=self.client_pbk, protocol_id="default", message=DefaultSerializer().encode(msg))
        self.client_mailbox.outbox.put(expected_envelope)
        actual_envelope = self.server_mailbox.inbox.get(timeout=2.0)
        logging.debug(actual_envelope)
        assert expected_envelope == actual_envelope

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello client")
        expected_envelope = Envelope(to=self.client_pbk, sender=self.server_pbk, protocol_id="default", message=DefaultSerializer().encode(msg))
        self.server_mailbox.outbox.put(expected_envelope)
        actual_envelope = self.client_mailbox.inbox.get(timeout=30.0)
        logging.debug(actual_envelope)
        assert expected_envelope == actual_envelope


    @classmethod
    def teardown_class(cls):
        """Tear down the test class."""
        cls.server_mailbox.disconnect()
        cls.client_mailbox.disconnect()

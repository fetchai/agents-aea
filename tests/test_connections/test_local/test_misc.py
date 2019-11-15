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

"""This module contains the tests of the local OEF node implementation."""

from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.mail.base import Envelope, MailBox
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer


def test_connection():
    """Test that two mailbox can connect to the node."""
    node = LocalNode()

    mailbox1 = MailBox([OEFLocalConnection("mailbox1", node)])
    mailbox2 = MailBox([OEFLocalConnection("mailbox2", node)])

    mailbox1.connect()
    mailbox2.connect()

    mailbox1.disconnect()
    mailbox2.disconnect()


def test_communication():
    """Test that two mailbox can communicate through the node."""
    with LocalNode() as node:

        mailbox1 = MailBox([OEFLocalConnection("mailbox1", node)])
        mailbox2 = MailBox([OEFLocalConnection("mailbox2", node)])

        mailbox1.connect()
        mailbox2.connect()

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg_bytes = DefaultSerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.CFP, query=None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.PROPOSE, proposal=[])
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.DECLINE)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert envelope.protocol_id == "default"
        assert msg.get("content") == b"hello"
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.CFP
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.PROPOSE
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.ACCEPT
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.DECLINE
        mailbox1.disconnect()
        mailbox2.disconnect()

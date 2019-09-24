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

"""This module contains the tests for Envelop,Mailbox,Inbox,Outbox of mail.base.py."""

from aea.mail.base import Envelope, MailBox, InBox, OutBox
from aea.protocols.base.message import Message
from aea.channels.local.connection import LocalNode, OEFLocalConnection
from aea.protocols.base.serialization import ProtobufSerializer
from queue import Queue


def test_envelope_initialisation():
    """Testing the envelope initialisation."""
    msg = Message(content='hello')
    message_bytes = ProtobufSerializer().encode(msg)
    envelope = Envelope(to="Agent1", sender="Agent0",
                        protocol_id="my_own_protocol", message=message_bytes)

    envelope.to = "ChangedAgent"
    envelope.sender = "ChangedSender"
    envelope.protocol_id = "my_changed_protocol"
    envelope.message = b"HelloWorld"

    assert envelope.to == "ChangedAgent", "Cannot set to value on Envelope"
    assert envelope.sender == "ChangedSender", "Cannot set sender value on Envelope"
    assert envelope.protocol_id == "my_changed_protocol", "Cannot set protocol_id on Envelope "
    assert envelope.message == b"HelloWorld", "Cannot set message on Envelope"

    assert envelope, "Cannot generate a new envelope"


def test_envelope_empty_receiver():
    """Tests what happens when we are passing wrong type of receiver."""
    to_adr = []
    msg = Message(content="hello")
    message_bytes = ProtobufSerializer().encode(msg)
    envelope = Envelope(to=to_adr, sender="Agent0",
                        protocol_id="my_own_protocol", message=message_bytes)
    assert envelope, "Receiver is the correct type"


def test_inbox_empty():
    """Tests if the inbox is empty."""
    my_queue = Queue()
    _inbox = InBox(my_queue)
    assert _inbox.empty(), "Inbox is not empty"


def test_inbox_nowait():
    """Tests the inbox without waiting."""
    msg = Message(content="hello")
    message_bytes = ProtobufSerializer().encode(msg)
    my_queue = Queue()
    my_queue.put(message_bytes)
    _inbox = InBox(my_queue)
    assert _inbox.get_nowait(), "Check for a message on the in queue and wait for no time."


def test_outbox_empty():
    """Test thet the outbox queue is empty."""
    my_queue = Queue()
    _outbox = OutBox(my_queue)
    assert _outbox.empty(), "The outbox is not empty"


def test_mailBox():
    """Tests if the mailbox is connected."""
    node = LocalNode()
    public_key_1 = "mailbox1"
    mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
    mailbox1.connect()
    assert mailbox1.is_connected, "Mailbox cannot connect to the specific Connection (OEFLocalConnection)"
    mailbox1.disconnect()

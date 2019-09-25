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
"""This module contains the tests for aea.aea.py."""
import os
import time
from threading import Thread

from aea.aea import AEA
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.base import Crypto
from aea.protocols.base import Message
from aea.protocols.base import ProtobufSerializer

from threading import Thread
import time
from pathlib import Path
from aea.crypto.helpers import _create_temporary_private_key_pem_path
from aea.mail.base import MailBox
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from tests.conftest import CUR_PATH


def test_initialise_aea():
    """Tests the initialisation of the AeA."""
    node = LocalNode()
    public_key_1 = "mailbox1"
    mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
    myAea = AEA("Agent0", mailbox1, directory=os.path.join(CUR_PATH, "data", "aea"))
    assert AEA("Agent0", mailbox1), "Agent is not inisialised"
    print(myAea.context)
    assert myAea.context == myAea._context, "Cannot access the Agent's Context"
    myAea.setup()
    assert myAea.resources is not None,\
        "Resources must not be None after setup"


def test_run_aea():
    """Test that the run of an AEA works correctly."""
    node = LocalNode()
    agent_name = "MyAgent"
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    agent = AEA(
        agent_name,
        mailbox,
        private_key_pem_path=private_key_pem_path,
        directory=os.path.join(CUR_PATH, "data", "aea"))
    t = Thread(target=agent.start)
    t.start()

    # handle proper message
    message = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    encoded_message = DefaultSerializer().encode(message)
    agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="error", message=encoded_message)

    # handle message with unknown protocol
    agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="unknown_protocol", message=b"hello")

    # handle bad encoded message
    agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="error", message=b"hello")

    # unsupported skill for protocol oef
    msg = FIPASerializer().encode(FIPAMessage(performative=FIPAMessage.Performative.ACCEPT,
                                              message_id=0, dialogue_id=0, destination=public_key, target=1))
    agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="fipa", message=msg)

    time.sleep(2.0)

    agent.stop()
    t.join()


def test_handle():
    """Tests handle method of an agent."""
    node = LocalNode()
    agent_name = "MyAgent"
    path = "/tests/aea/"
    private_key_pem_path = _create_temporary_private_key_pem_path()
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    mailbox = MailBox(OEFLocalConnection(public_key, node))

#   msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
#   message_bytes = DefaultSerializer().encode(msg)

    msg = Message(message="hello")
    message_bytes = ProtobufSerializer().encode(msg)

    envelope = Envelope(
        to=public_key,
        sender="Agent0",
        protocol_id="Unknown_protocol_id",
        message=message_bytes)

    agent = AEA(
        agent_name,
        mailbox,
        private_key_pem_path=private_key_pem_path,
        directory=str(Path(".").absolute()) + path)
    t = Thread(target=agent.start)
    t.start()
    agent.outbox.put(envelope)
    time.sleep(1)
    agent.stop()
    t.join()

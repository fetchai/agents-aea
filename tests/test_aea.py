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

from aea.aea import AEA
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.helpers import _create_temporary_private_key_pem_path
from aea.crypto.base import Crypto

from threading import Thread
import time
from pathlib import Path


def test_initialiseAeA():
    """Tests the initialisation of the AeA."""
    node = LocalNode()
    public_key_1 = "mailbox1"
    path = "/tests/aea/"
    mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
    myAea = AEA("Agent0", mailbox1, directory=str(Path(".").absolute()) + path)
    assert AEA("Agent0", mailbox1), "Agent is not inisialised"
    print(myAea.context)
    assert myAea.context == myAea._context, "Cannot access the Agent's Context"
    myAea.setup()
    assert myAea.resources is not None,\
        "Resources must not be None after setup"


def test_act():
    """Tests the act function of the AeA."""
    node = LocalNode()
    agent_name = "MyAgent"
    path = "/tests/data/dummy_aea/"
    private_key_pem_path = _create_temporary_private_key_pem_path()
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    agent = AEA(
        agent_name,
        mailbox,
        private_key_pem_path=private_key_pem_path,
        directory=str(Path(".").absolute()) + path)
    t = Thread(target=agent.start)
    t.start()
    time.sleep(1)

    behaviour = agent.resources.behaviour_registry.fetch("dummy")
    assert behaviour[0].nb_act_called > 0, "Act() wasn't called"
    agent.stop()
    t.join()


def test_react():
    """Tests income messages."""
    node = LocalNode()
    agent_name = "MyAgent"
    path = "/tests/data/dummy_aea/"
    private_key_pem_path = _create_temporary_private_key_pem_path()
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    message_bytes = DefaultSerializer().encode(msg)

    envelope = Envelope(
        to="Agent1",
        sender=public_key,
        protocol_id="default",
        message=message_bytes)

    agent = AEA(
        agent_name,
        mailbox,
        private_key_pem_path=private_key_pem_path,
        directory=str(Path(".").absolute()) + path)
    t = Thread(target=agent.start)
    t.start()
    agent.mailbox.inbox._queue.put(envelope)
    time.sleep(1)
    handler = agent.resources.handler_registry.fetch_by_skill('default', "dummy")
    assert envelope in handler.handled_envelopes, "The envelope is not inside the handled_envelopes."
    agent.stop()
    t.join()


def test_handle():
    """Tests handle method of an agent."""
    node = LocalNode()
    agent_name = "MyAgent"
    path = "/tests/data/dummy_aea/"
    private_key_pem_path = _create_temporary_private_key_pem_path()
    crypto = Crypto(private_key_pem_path=private_key_pem_path)
    public_key = crypto.public_key
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    message_bytes = DefaultSerializer().encode(msg)

    envelope = Envelope(
        to="Agent1",
        sender=public_key,
        protocol_id="unknown_protocl",
        message=message_bytes)

    agent = AEA(
        agent_name,
        mailbox,
        private_key_pem_path=private_key_pem_path,
        directory=str(Path(".").absolute()) + path)
    t = Thread(target=agent.start)
    t.start()
    agent.mailbox.inbox._queue.put(envelope)
    env = agent.mailbox.outbox._queue.get(block=True, timeout=1)
    assert env.protocol_id == "error", "The envelope is not the expected protocol"
    agent.stop()
    t.join()

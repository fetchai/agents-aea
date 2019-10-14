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
from pathlib import Path
from threading import Thread

from aea.aea import AEA
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from .conftest import CUR_PATH


def test_initialise_AEA():
    """Tests the initialisation of the AEA."""
    node = LocalNode()
    public_key_1 = "mailbox1"
    mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path})
    my_AEA = AEA("Agent0", mailbox1, wallet, directory=str(Path(CUR_PATH, "aea")))
    assert AEA("Agent0", mailbox1, wallet), "Agent is not initialised"
    assert my_AEA.context == my_AEA._context, "Cannot access the Agent's Context"
    my_AEA.setup()
    assert my_AEA.resources is not None,\
        "Resources must not be None after setup"


def test_act():
    """Tests the act function of the AEA."""
    node = LocalNode()
    agent_name = "MyAgent"
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path})
    public_key = wallet.public_keys['default']
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    agent = AEA(
        agent_name,
        mailbox,
        wallet,
        directory=str(Path(CUR_PATH, "data", "dummy_aea")))
    t = Thread(target=agent.start)
    try:
        t.start()
        time.sleep(1)

        behaviour = agent.resources.behaviour_registry.fetch("dummy")
        assert behaviour[0].nb_act_called > 0, "Act() wasn't called"
    finally:
        agent.stop()
        t.join()


def test_react():
    """Tests income messages."""
    node = LocalNode()
    agent_name = "MyAgent"
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path})
    public_key = wallet.public_keys['default']
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
        wallet,
        directory=str(Path(CUR_PATH, "data", "dummy_aea")))
    t = Thread(target=agent.start)
    try:
        t.start()
        agent.mailbox.inbox._queue.put(envelope)
        time.sleep(1)
        handler = agent.resources \
            .handler_registry.fetch_by_skill('default', "dummy")
        assert msg in handler.handled_messages, \
            "The message is not inside the handled_messages."
    finally:
        agent.stop()
        t.join()


def test_handle():
    """Tests handle method of an agent."""
    node = LocalNode()
    agent_name = "MyAgent"
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path})
    public_key = wallet.public_keys['default']
    mailbox = MailBox(OEFLocalConnection(public_key, node))

    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    message_bytes = DefaultSerializer().encode(msg)

    envelope = Envelope(
        to="Agent1",
        sender=public_key,
        protocol_id="unknown_protocol",
        message=message_bytes)

    agent = AEA(
        agent_name,
        mailbox,
        wallet,
        directory=str(Path(CUR_PATH, "data", "dummy_aea")))
    t = Thread(target=agent.start)
    try:
        t.start()
        agent.mailbox.inbox._queue.put(envelope)
        env = agent.mailbox.outbox._queue.get(block=True, timeout=5.0)
        assert env.protocol_id == "default", \
            "The envelope is not the expected protocol (Unsupported protocol)"

        #   DECODING ERROR
        msg = "hello".encode("utf-8")
        envelope = Envelope(
            to=public_key,
            sender=public_key,
            protocol_id='default',
            message=msg)
        agent.mailbox.inbox._queue.put(envelope)
        #   UNSUPPORTED SKILL
        msg = FIPASerializer().encode(
            FIPAMessage(performative=FIPAMessage.Performative.ACCEPT,
                        message_id=0,
                        dialogue_id=0,
                        destination=public_key,
                        target=1))
        envelope = Envelope(
            to=public_key,
            sender=public_key,
            protocol_id="fipa",
            message=msg)
        agent.mailbox.inbox._queue.put(envelope)
    finally:
        agent.stop()
        t.join()

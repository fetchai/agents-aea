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

"""This test module contains the tests for the OEF communication using an OEF."""
import time
from threading import Thread

from aea.agent import Agent
from aea.channel.oef import OEFMailBox
from aea.crypto.base import Crypto
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer


class TAgent(Agent):
    """Implement a test agent."""

    def setup(self) -> None:
        """Set up the agent."""
        pass

    def act(self) -> None:
        """Do actions."""
        pass

    def react(self) -> None:
        """Do reactions."""
        pass

    def update(self) -> None:
        """Update the agent's state."""
        pass

    def teardown(self) -> None:
        """Teardown the agent."""
        pass


def test_start_agent(network_node):
    """Test that the start method works as expected."""
    crypto = Crypto()
    mailbox = OEFMailBox(crypto.public_key, oef_addr="127.0.0.1", oef_port=10000)
    agent = TAgent("my_agent", oef_addr="127.0.0.1", oef_port=10000)
    agent.mailbox = mailbox

    job = Thread(target=agent.start)
    job.start()

    time.sleep(3.0)
    assert agent.mailbox.is_connected
    agent.stop()


def test_send_message(network_node):
    """Test that an agent can send a message."""
    crypto = Crypto()
    mailbox = OEFMailBox(crypto.public_key, oef_addr="127.0.0.1", oef_port=10000)
    agent = TAgent("my_agent", oef_addr="127.0.0.1", oef_port=10000)
    agent.mailbox = mailbox

    job = Thread(target=agent.start)
    job.start()

    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    agent.outbox.put_message(to=crypto.public_key, sender=crypto.public_key, protocol_id=DefaultMessage.protocol_id,
                             message=DefaultSerializer().encode(msg))
    envelope = agent.inbox.get(block=True, timeout=5.0)
    actual_message = DefaultSerializer().decode(envelope.message)
    assert actual_message.get("content") == b"hello"

    agent.stop()
    job.join()

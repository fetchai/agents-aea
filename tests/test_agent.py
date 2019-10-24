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

"""This module contains the tests of the agent module."""
import os
import time
from threading import Thread

from aea.agent import Agent, AgentState
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, InBox, OutBox
from .conftest import CUR_PATH


class DummyAgent(Agent):
    """A dummy agent for testing."""

    def __init__(self, *args, **kwargs):
        """Initialize the agent."""
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the agent."""
        pass

    def act(self) -> None:
        """Act."""
        pass

    def react(self) -> None:
        """React to events."""
        pass

    def update(self) -> None:
        """Update the state of the agent."""
        pass

    def teardown(self) -> None:
        """Tear down the agent."""
        pass


def test_run_agent():
    """Test that we can set up and then run the agent."""
    agent_name = "dummyagent"
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path}, {})
    agent = DummyAgent(agent_name, wallet)
    mailbox = MailBox(OEFLocalConnection("mypbk", LocalNode()))
    agent.mailbox = mailbox
    assert agent.name == agent_name
    assert isinstance(agent.wallet, Wallet)
    assert agent.agent_state == AgentState.INITIATED,\
        "Agent state must be 'initiated'"

    agent.mailbox.connect()
    assert agent.agent_state == AgentState.CONNECTED,\
        "Agent state must be 'connected'"

    assert isinstance(agent.inbox, InBox)
    assert isinstance(agent.outbox, OutBox)

    agent_thread = Thread(target=agent.start)
    agent_thread.start()
    time.sleep(1)

    try:
        assert agent.agent_state == AgentState.RUNNING,\
            "Agent state must be 'running'"
    finally:
        agent.stop()
        agent.mailbox.disconnect()
        agent_thread.join()

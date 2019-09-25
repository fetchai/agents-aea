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
import time
from threading import Timer, Thread
from unittest import mock
from unittest.mock import MagicMock

from aea.agent import Agent, AgentState
from aea.channels.local.connection import OEFLocalConnection, LocalNode
from aea.crypto.base import Crypto
from aea.mail.base import MailBox, InBox, OutBox


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
    agent = DummyAgent(agent_name)
    mailbox = MailBox(OEFLocalConnection("mypbk", LocalNode()))
    agent.mailbox = mailbox
    try:
        assert agent.name == agent_name
        assert isinstance(agent.crypto, Crypto)
        assert agent.agent_state == AgentState.INITIATED

        agent.mailbox.connect()
        assert agent.agent_state == AgentState.CONNECTED

        assert isinstance(agent.inbox, InBox)
        assert isinstance(agent.outbox, OutBox)

        with mock.patch.object(agent, 'setup') as mock_setup, \
                mock.patch.object(agent, 'act') as mock_act, \
                mock.patch.object(agent, 'react') as mock_react, \
                mock.patch.object(agent, 'update') as mock_update, \
                mock.patch.object(agent, 'teardown') as mock_teardown:

            stopper = Timer(2.0, function=agent.stop)
            stopper.start()
            agent_thread = Thread(target=agent.start)
            agent_thread.start()

            time.sleep(0.1)
            assert agent.agent_state == AgentState.RUNNING

            stopper.join()
            agent_thread.join()

            mock_setup.assert_called_once()
            mock_act.assert_called()
            mock_react.assert_called()
            mock_teardown.assert_called()
            mock_teardown.assert_called_once()
    finally:
        agent.stop()

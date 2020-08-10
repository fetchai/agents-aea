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
import asyncio
from threading import Thread

import pytest

from aea.agent import Agent, Identity
from aea.runtime import RuntimeStates

from packages.fetchai.connections.local.connection import LocalNode

from tests.common.utils import wait_for_condition

from .conftest import _make_local_connection


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
    with LocalNode() as node:
        agent_name = "dummyagent"
        agent_address = "some_address"
        identity = Identity(agent_name, address=agent_address)
        oef_local_connection = _make_local_connection(agent_address, node)
        oef_local_connection._local_node = node

        agent = DummyAgent(
            identity, [oef_local_connection], loop=asyncio.new_event_loop()
        )
        agent_thread = Thread(target=agent.start)
        assert agent.state == RuntimeStates.stopped
        agent_thread.start()
        try:
            wait_for_condition(
                lambda: agent.state == RuntimeStates.starting,
                timeout=10,
                error_msg="Agent state must be 'starting'",
            )
            wait_for_condition(
                lambda: agent.state == RuntimeStates.running,
                timeout=10,
                error_msg="Agent state must be 'running'",
            )
        finally:
            agent.stop()
            assert agent.state == RuntimeStates.stopped
            agent_thread.join()


def test_runtime_modes():
    """Test runtime modes are set."""
    agent_name = "dummyagent"
    agent_address = "some_address"
    identity = Identity(agent_name, address=agent_address)
    agent = DummyAgent(identity, [],)

    assert not agent.is_running
    assert agent.is_stopped

    agent._runtime_mode = "not exists"

    with pytest.raises(ValueError):
        agent._get_runtime_class()

    agent._loop_mode = "not exists"

    with pytest.raises(ValueError):
        agent._get_main_loop_class()

    assert agent._loop_mode == agent.loop_mode

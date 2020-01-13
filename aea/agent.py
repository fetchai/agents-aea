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

"""This module contains the implementation of a template agent."""

import logging
import time
from abc import abstractmethod, ABC
from asyncio import AbstractEventLoop
from enum import Enum
from typing import Optional, List

from aea.connections.base import Connection
from aea.crypto.wallet import Wallet
from aea.mail.base import InBox, OutBox, Multiplexer

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Enumeration for an agent state."""

    INITIATED = "initiated"
    CONNECTED = "connected"
    RUNNING = "running"


class Liveness:
    """Determines the liveness of the agent."""

    def __init__(self):
        """Instantiate the liveness."""
        self._is_stopped = True

    @property
    def is_stopped(self) -> bool:
        """Check whether the liveness is stopped."""
        return self._is_stopped


class Agent(ABC):
    """This class implements a template agent."""

    def __init__(self, name: str,
                 connections: List[Connection],
                 wallet: Wallet,
                 loop: Optional[AbstractEventLoop] = None,
                 timeout: float = 1.0,
                 debug: bool = False,
                 programmatic: bool = False) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param connections: the list of connections of the agent.
        :param wallet: the crypto wallet of the agent.
        :param loop: the event loop to run the connections.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param programmatic: if True, run the agent in programmatic mode (skips loading of resources from directory).

        :return: None
        """
        self._name = name
        self._connections = connections
        self._wallet = wallet

        self._multiplexer = Multiplexer(self._connections, loop=loop)
        self._inbox = InBox(self._multiplexer)
        self._outbox = OutBox(self._multiplexer)
        self._liveness = Liveness()
        self._timeout = timeout

        self.debug = debug
        self.programmatic = programmatic

    @property
    def multiplexer(self) -> Multiplexer:
        """Get the multiplexer."""
        return self._multiplexer

    @property
    def inbox(self) -> InBox:
        """Get the inbox."""
        return self._inbox

    @property
    def outbox(self) -> OutBox:
        """Get the outbox."""
        return self._outbox

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def wallet(self) -> Wallet:
        """Get the wallet."""
        return self._wallet

    @property
    def liveness(self) -> Liveness:
        """Get the liveness."""
        return self._liveness

    @property
    def agent_state(self) -> AgentState:
        """
        Get the state of the agent.

        In particular, it can be one of the following states:
        - AgentState.INITIATED: when the Agent object has been created.
        - AgentState.CONNECTED: when the agent is connected.
        - AgentState.RUNNING: when the agent is running.

        :return the agent state.
        :raises ValueError: if the state does not satisfy any of the foreseen conditions.
        """
        if self.multiplexer is not None and not self.multiplexer.connection_status.is_connected:
            return AgentState.INITIATED
        elif self.multiplexer.connection_status.is_connected and self.liveness.is_stopped:
            return AgentState.CONNECTED
        elif self.multiplexer.connection_status.is_connected and not self.liveness.is_stopped:
            return AgentState.RUNNING
        else:
            raise ValueError("Agent state not recognized.")  # pragma: no cover

    def start(self) -> None:
        """
        Start the agent.

        :return: None
        """
        if not self.debug and not self.multiplexer.connection_status.is_connected:
            self.multiplexer.connect()

        logger.debug("[{}]: Calling setup method...".format(self.name))
        self.setup()

        self.liveness._is_stopped = False
        self._run_main_loop()

    def _run_main_loop(self) -> None:
        """
        Run the main loop of the agent.

        :return: None
        """
        logger.debug("[{}]: Start processing messages...".format(self.name))
        while not self.liveness.is_stopped:
            self.act()
            time.sleep(self._timeout)
            self.react()
            self.update()
        logger.debug("[{}]: Exiting main loop...".format(self.name))

    def stop(self) -> None:
        """
        Stop the agent.

        :return: None
        """
        self.liveness._is_stopped = True
        logger.debug("[{}]: Calling teardown method...".format(self.name))
        self.teardown()

        logger.debug("[{}]: Stopping message processing...".format(self.name))
        if self.multiplexer.connection_status.is_connected:
            self.multiplexer.disconnect()

    @abstractmethod
    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """

    @abstractmethod
    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """

    @abstractmethod
    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """

    @abstractmethod
    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """

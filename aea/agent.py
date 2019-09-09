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
from enum import Enum
from typing import Optional

from aea.crypto.base import Crypto
from aea.mail.base import InBox, OutBox, MailBox

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
                 private_key_pem_path: Optional[str] = None,
                 timeout: float = 1.0,
                 debug: bool = False) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param private_key_pem_path: the path to the private key of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.

        :return: None
        """
        self._name = name
        self._crypto = Crypto(private_key_pem_path=private_key_pem_path)
        self._liveness = Liveness()
        self._timeout = timeout

        self.debug = debug

        self.mailbox = None  # type: Optional[MailBox]

    @property
    def inbox(self) -> InBox:
        """Get the inbox."""
        assert self.mailbox is not None, "Cannot retrieve inbox. No mailbox specified."
        return self.mailbox.inbox

    @property
    def outbox(self) -> OutBox:
        """Get the outbox."""
        assert self.mailbox is not None, "Cannot retrieve outbox. No mailbox specified."
        return self.mailbox.outbox

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def crypto(self) -> Crypto:
        """Get the crypto."""
        return self._crypto

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
        if self.mailbox is None or not self.mailbox.is_connected:
            return AgentState.INITIATED
        elif self.mailbox.is_connected and self.liveness.is_stopped:
            return AgentState.CONNECTED
        elif self.mailbox.is_connected and not self.liveness.is_stopped:
            return AgentState.RUNNING
        else:
            raise ValueError("Agent state not recognized.")

    def start(self) -> None:
        """
        Start the agent.

        :return: None
        """
        assert self.mailbox is not None, "Cannot call start without mailbox instantiated."
        if not self.debug and not self.mailbox.is_connected:
            self.mailbox.connect()

        self.liveness._is_stopped = False
        self._run_main_loop()

    def _run_main_loop(self) -> None:
        """
        Run the main loop of the agent.

        :return: None
        """
        logger.debug("[{}]: Calling setup method...".format(self.name))
        self.setup()

        logger.debug("[{}]: Start processing messages...".format(self.name))
        while not self.liveness.is_stopped:
            self.act()
            time.sleep(self._timeout)
            self.react()
            self.update()

        logger.debug("[{}]: Calling teardown method...".format(self.name))
        self.teardown()

        self.stop()
        logger.debug("[{}]: Exiting main loop...".format(self.name))

    def stop(self) -> None:
        """
        Stop the agent.

        :return: None
        """
        assert self.mailbox is not None, "Cannot call stop without mailbox instantiated."
        logger.debug("[{}]: Stopping message processing...".format(self.name))
        self.liveness._is_stopped = True
        if self.mailbox.is_connected:
            self.mailbox.disconnect()

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

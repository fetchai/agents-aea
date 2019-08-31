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
from typing import Dict, List
from typing import Optional

from aea.crypto.base import Crypto
from aea.mail.base import InBox, OutBox, MailBox
from aea.mail.base import ProtocolId, Envelope

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
                 timeout: Optional[float] = 1.0,
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
    def inbox(self) -> Optional[InBox]:
        """Get the inbox."""
        return self.mailbox.inbox if self.mailbox else None

    @property
    def outbox(self) -> Optional[OutBox]:
        """Get the outbox."""
        return self.mailbox.outbox if self.mailbox else None

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


SkillId = str


class Behaviour(ABC):
    """This class implements an abstract behaviour."""

    @abstractmethod
    def act(self) -> None:
        """
        Implement the behaviour.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the behaviour teardown.

        :return: None
        """


class Handler(ABC):
    """This class implements an abstract behaviour."""

    @abstractmethod
    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


TaskId = str


class Task(ABC):
    """This class implements an abstract task."""

    @abstractmethod
    def execute(self) -> None:
        """
        Run the task logic.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the task.

        :return: None
        """


class Registry(ABC):
    """This class implements an abstract registry."""

    @abstractmethod
    def populate(self) -> None:
        """
        Load into the registry as specified in the config and apply consistency checks.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """


class ProtocolRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._protocols = []  # type: List

    def populate(self) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_protocol(self, envelope: Envelope) -> Optional[ProtocolId]:
        """
        Fetch the protocol for the envelope.

        :pass envelope: the envelope
        :return: the protocol id or None if the protocol is not registered
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._protocols = []


class HandlerRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, Handler]

    def populate(self) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_handler(self, protocol_id: ProtocolId) -> Handler:
        """
        Fetch the handler for the protocol_id.

        :param protocol_id: the protocol id
        :return: the handler
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for handler in self._handlers:
            handler.teardown()
        self._handlers = {}


class BehaviourRegistry(Registry):
    """This class implements the behaviour registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, Behaviour]

    def populate(self) -> None:
        """
        Load the behaviours as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_behaviours(self) -> Optional[List[Behaviour]]:
        """
        Return a list of behaviours for processing.

        :return: the list of behaviours
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for behaviour in self._behaviours:
            behaviour.teardown()
        self._behaviours = {}


class TaskRegistry(Registry):
    """This class implements the task registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._tasks = {}  # type: Dict[TaskId, Task]

    def populate(self) -> None:
        """
        Load the tasks as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_tasks(self) -> Optional[List[Task]]:
        """
        Return a list of tasks for processing.

        :return: a list of tasks.
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for task in self._tasks:
            task.teardown()
        self._tasks = {}


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 oef_addr: str,
                 oef_port: int = 10000,
                 private_key_pem_path: Optional[str] = None,
                 timeout: Optional[float] = 1.0,
                 debug: bool = False) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param oef_addr: TCP/IP address of the OEF Agent
        :param oef_port: TCP/IP port of the OEF Agent
        :param private_key_pem_path: the path to the private key of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.

        :return: None
        """
        super().__init__(name=name, oef_addr=oef_addr, private_key_pem_path=private_key_pem_path, timeout=timeout, debug=debug)

        self._protocol_registry = ProtocolRegistry()
        self._handler_registry = HandlerRegistry()
        self._behaviour_registry = BehaviourRegistry()

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        self._protocol_registry.populate()
        self._handler_registry.populate()
        self._behaviour_registry.populate()

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        for behaviour in self._behaviour_registry.fetch_behaviours():
            behaviour.act()

    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """
        counter = 0
        while (not self.inbox.empty() and counter < self.max_reactions):
            counter += 1
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            if envelope is not None:
                protocol_id = self._protocol_registry.fetch_protocol(envelope)
                if protocol_id is not None:
                    handler = self._handler_registry.fetch_handler(protocol_id)
                    handler.handle_envelope(envelope)

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        for task in self._task_registry.fetch_tasks():
            task.execute()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        self._behaviour_registry.teardown()
        self._handler_registry.teardown()
        self._protocol_registry.teardown()

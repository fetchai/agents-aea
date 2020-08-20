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


"""This module contains the implementation of a generic agent."""
import datetime
import logging
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from multiprocessing.pool import AsyncResult
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type

from aea.connections.base import Connection
from aea.identity.base import Identity
from aea.multiplexer import InBox, OutBox
from aea.runtime import AsyncRuntime, BaseRuntime, RuntimeStates, ThreadedRuntime


logger = logging.getLogger(__name__)


class Agent(ABC):
    """This class provides an abstract base class for a generic agent."""

    RUNTIMES: Dict[str, Type[BaseRuntime]] = {
        "async": AsyncRuntime,
        "threaded": ThreadedRuntime,
    }
    DEFAULT_RUNTIME: str = "threaded"

    def __init__(
        self,
        identity: Identity,
        connections: List[Connection],
        loop: Optional[AbstractEventLoop] = None,
        timeout: float = 1.0,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
    ) -> None:
        """
        Instantiate the agent.

        :param identity: the identity of the agent.
        :param connections: the list of connections of the agent.
        :param loop: the event loop to run the connections.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param loop_mode: loop_mode to choose agent run loop.
        :param runtime_mode: runtime mode to up agent.

        :return: None
        """
        self._connections = connections
        self._identity = identity
        self._loop_mode = loop_mode
        self._timeout = timeout
        self._tick = 0
        self._runtime_mode = runtime_mode or self.DEFAULT_RUNTIME
        runtime_cls = self._get_runtime_class()
        self._runtime: BaseRuntime = runtime_cls(agent=self, loop=loop)

        self._inbox = InBox(self.runtime.multiplexer)
        self._outbox = OutBox(self.runtime.multiplexer, self._identity.address)

    @property
    def active_connections(self) -> List[Connection]:
        """Return list of active connections."""
        return self._connections

    @property
    def is_running(self) -> bool:
        """Get running state of the runtime and agent."""
        return self.runtime.is_running

    @property
    def is_stopped(self) -> bool:
        """Get running state of the runtime and agent."""
        return self.runtime.is_stopped

    def _get_runtime_class(self) -> Type[BaseRuntime]:
        """Get runtime class based on runtime mode."""
        if self._runtime_mode not in self.RUNTIMES:
            raise ValueError(
                f"Runtime `{self._runtime_mode} is not supported. valid are: `{list(self.RUNTIMES.keys())}`"
            )
        return self.RUNTIMES[self._runtime_mode]

    def enqueue_task(
        self, func: Callable, args: Sequence = (), kwds: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Enqueue a task with the task manager.

        :param func: the callable instance to be enqueued
        :param args: the positional arguments to be passed to the function.
        :param kwds: the keyword arguments to be passed to the function.
        :return the task id to get the the result.
        :raises ValueError: if the task manager is not running.
        """
        return self.runtime.task_manager.enqueue_task(func, args, kwds)

    def get_task_result(self, task_id: int) -> AsyncResult:
        """
        Get the result from a task.

        :return: async result for task_id
        """
        return self.runtime.task_manager.get_task_result(task_id)

    def _get_multiplexer_setup_options(  # pylint: disable=no-self-use # cause overrided in AEA
        self,
    ) -> Optional[Dict]:
        """
        Get dict of multiplexer setup options.

        :return: dict of kwargs for Multipelxer.setup
        """
        return {"connections": self.active_connections}

    @property
    def identity(self) -> Identity:
        """Get the identity."""
        return self._identity

    @property
    def inbox(self) -> InBox:  # pragma: nocover
        """
        Get the inbox.

        The inbox contains Envelopes from the Multiplexer.
        The agent can pick these messages for processing.
        """
        return self._inbox

    @property
    def outbox(self) -> OutBox:  # pragma: nocover
        """
        Get the outbox.

        The outbox contains Envelopes for the Multiplexer.
        Envelopes placed in the Outbox are processed by the Multiplexer.
        """
        return self._outbox

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self.identity.name

    @property
    def tick(self) -> int:  # pragma: nocover
        """
        Get the tick or agent loop count.

        Each agent loop (one call to each one of act(), react(), update()) increments the tick.
        """
        return self._tick

    @property
    def timeout(self) -> float:
        """Get the time in (fractions of) seconds to time out an agent between act and react."""
        return self._timeout

    @property
    def loop_mode(self) -> str:
        """Get the agent loop mode."""
        return self._loop_mode or self.runtime.DEFAULT_RUN_LOOP

    @property
    def runtime(self) -> BaseRuntime:
        """Get the runtime."""
        return self._runtime

    def start(self) -> None:
        """
        Start the agent.

        Performs the following:

        - calls connect() on the multiplexer (unless in debug mode), and
        - calls setup(), and
        - calls start() on the liveness, and
        - enters the agent main loop.

        While the liveness of the agent is not stopped it continues to loop over:

        - increment the tick,
        - call to act(),
        - sleep for specified timeout,
        - call to react(),
        - call to update().

        :return: None
        """
        self.runtime.start()

    def start_setup(self) -> None:
        """
        Set up Agent on start.

        - connect Multiplexer
        - call agent.setup
        - set liveness to started

        :return: None
        """
        logger.debug("[{}]: Calling setup method...".format(self.name))
        self.setup()

    def stop(self) -> None:
        """
        Stop the agent.

        Performs the following:

        - calls stop() on the liveness, and
        - calls teardown(), and
        - calls disconnect() on the multiplexer.

        :return: None
        """
        self.runtime.stop()

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
        React to events.

        :return: None
        """

    @abstractmethod
    def update(self) -> None:
        """
        Update the internals of the agent which are not exposed to the skills.

        :return None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """

    @property
    def state(self) -> RuntimeStates:
        """
        Get state of the agent's runtime.

        :return: RuntimeStates
        """
        return self._runtime.state

    def _get_periodic_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        """
        Get all periodic tasks for agent.

        :return: dict of callable with period specified
        """
        return {self.act: (self.tick, None)}

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
"""This module contains the implementation of an agent loop using asyncio."""
import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from enum import Enum
from functools import partial
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)

from aea.exceptions import AEAException
from aea.helpers.async_utils import (
    AsyncState,
    PeriodicCaller,
    ensure_loop,
)
from aea.helpers.logging import WithLogger
from aea.multiplexer import InBox
from aea.skills.base import Behaviour


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from aea.aea import AEA  # pragma: no cover
    from aea.agent import Agent  # pragma: no cover


class BaseAgentLoop(WithLogger, ABC):
    """Base abstract  agent loop class."""

    def __init__(
        self, agent: "Agent", loop: Optional[AbstractEventLoop] = None
    ) -> None:
        """Init loop.

        :params agent: Agent or AEA to run.
        :params loop: optional asyncio event loop. if not specified a new loop will be created.
        """
        WithLogger.__init__(self, logger)
        self._agent: "Agent" = agent
        self.set_loop(ensure_loop(loop))
        self._tasks: List[asyncio.Task] = []
        self._state: AsyncState = AsyncState()
        self._exceptions: List[Exception] = []

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """Set event loop and all event loopp related objects."""
        self._loop: AbstractEventLoop = loop

    def start(self) -> None:
        """Start agent loop synchronously in own asyncio loop."""
        self._loop.run_until_complete(self.run_loop())

    async def run_loop(self) -> None:
        """Run agent loop."""
        self.logger.debug("agent loop started")
        self._state.set(AgentLoopStates.started)
        self._set_tasks()
        try:
            await self._gather_tasks()
        except (CancelledError, KeyboardInterrupt):
            await self.wait_run_loop_stopped()
            if self._exceptions:
                raise self._exceptions[0]
        logger.debug("agent loop stopped")
        self._state.set(AgentLoopStates.stopped)

    async def _gather_tasks(self) -> None:
        """Wait till first task exception."""
        await asyncio.gather(*self._tasks, loop=self._loop)

    @abstractmethod
    def _set_tasks(self) -> None:  # pragma: nocover
        """Set run loop tasks."""
        raise NotImplementedError

    async def wait_run_loop_stopped(self) -> None:
        """Wait all tasks stopped."""
        return await asyncio.gather(
            *self._tasks, loop=self._loop, return_exceptions=True
        )

    def stop(self) -> None:
        """Stop agent loop."""
        self._state.set(AgentLoopStates.stopping)
        logger.debug("agent loop stopping!")
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._stop_tasks)
        else:

            async def stop():
                self._stop_tasks()
                await self.wait_run_loop_stopped()

            self._loop.run_until_complete(stop())

    def _stop_tasks(self) -> None:
        """Cancel all tasks."""
        for task in self._tasks:
            if task.done():
                continue
            task.cancel()

    @property
    def is_running(self) -> bool:
        """Get running state of the loop."""
        return self._state.get() == AgentLoopStates.started


class AgentLoopException(AEAException):
    """Exception for agent loop runtime errors."""


class AgentLoopStates(Enum):
    """Internal agent loop states."""

    initial = None
    started = "started"
    stopped = "stopped"
    stopping = "stopping"
    error = "error"


class AsyncAgentLoop(BaseAgentLoop):
    """Asyncio based agent loop suitable only for AEA."""

    NEW_BEHAVIOURS_PROCESS_SLEEP = 1  # check new behaviours registered every second.

    def __init__(self, agent: "AEA", loop: AbstractEventLoop = None):
        """
        Init agent loop.

        :param agent: AEA instance
        :param loop: asyncio loop to use. optional
        """
        super().__init__(agent=agent, loop=loop)
        self._agent: "AEA" = self._agent

        self._behaviours_registry: Dict[Behaviour, PeriodicCaller] = {}

    def _behaviour_exception_callback(self, fn: Callable, exc: Exception) -> None:
        """
        Call on behaviour's act exception.

        :param fn: behaviour's act
        :param: exc: Exception  raised

        :return: None
        """
        self.logger.exception(
            f"Loop: Exception: `{exc}` occured during `{fn}` processing"
        )
        self._exceptions.append(exc)
        self._state.set(AgentLoopStates.error)

    def _register_behaviour(self, behaviour: Behaviour) -> None:
        """
        Register behaviour to run periodically.

        :param behaviour: Behaviour object

        :return: None
        """
        if behaviour in self._behaviours_registry:
            # already registered
            return

        periodic_caller = PeriodicCaller(
            partial(
                self._agent._execution_control,  # pylint: disable=protected-access # TODO: refactoring!
                behaviour.act_wrapper,
                behaviour,
            ),
            behaviour.tick_interval,
            behaviour.start_at,
            self._behaviour_exception_callback,
            self._loop,
        )
        self._behaviours_registry[behaviour] = periodic_caller
        periodic_caller.start()
        self.logger.debug(f"Behaviour {behaviour} registered.")

    def _register_all_behaviours(self) -> None:
        """Register all AEA behaviours to run periodically."""
        for behaviour in self._agent.active_behaviours:
            self._register_behaviour(behaviour)

    def _unregister_behaviour(self, behaviour: Behaviour) -> None:
        """
        Unregister periodic execution of the behaviour.

        :param behaviour: Behaviour to schedule periodic execution.
        :return: None
        """
        periodic_caller = self._behaviours_registry.pop(behaviour, None)
        if periodic_caller is None:  # pragma: nocover
            return
        periodic_caller.stop()

    def _stop_all_behaviours(self) -> None:
        """Unregister periodic execution of all registered behaviours."""
        for behaviour in list(self._behaviours_registry.keys()):
            self._unregister_behaviour(behaviour)

    async def _task_wait_for_error(self) -> None:
        """Wait for error and raise first."""
        await self._state.wait(AgentLoopStates.error)
        raise self._exceptions[0]

    def _stop_tasks(self):
        """Cancel all tasks and stop behaviours registered."""
        BaseAgentLoop._stop_tasks(self)
        self._stop_all_behaviours()

    def _set_tasks(self):
        """Set run loop tasks."""
        self._tasks = self._create_tasks()
        self.logger.debug("tasks created!")

    def _create_tasks(self) -> List[Task]:
        """
        Create tasks.

        :return: list of asyncio Tasks
        """
        tasks = [
            self._task_process_inbox(),
            self._task_process_internal_messages(),
            self._task_process_new_behaviours(),
            self._task_wait_for_error(),
        ]
        return list(map(self._loop.create_task, tasks))  # type: ignore  # some issue with map and create_task

    async def _task_process_inbox(self) -> None:
        """Process incoming messages."""
        inbox: InBox = self._agent.inbox
        self.logger.info("Start processing messages...")
        while self.is_running:
            await inbox.async_wait()
            self._agent.react()

    async def _task_process_internal_messages(self) -> None:
        """Process decision maker's internal messages."""
        queue = self._agent.decision_maker.message_out_queue
        while self.is_running:
            msg = await queue.async_get()
            # TODO: better interaction with agent's internal messages
            self._agent.filter._process_internal_message(  # pylint: disable=protected-access # TODO: refactoring!
                msg
            )

    async def _task_process_new_behaviours(self) -> None:
        """Process new behaviours added to skills in runtime."""
        while self.is_running:
            # TODO: better handling internal messages for skills internal updates
            self._agent.filter._handle_new_behaviours()  # pylint: disable=protected-access # TODO: refactoring!
            self._register_all_behaviours()  # re register, cause new may appear
            await asyncio.sleep(self.NEW_BEHAVIOURS_PROCESS_SLEEP)


class SyncAgentLoop(BaseAgentLoop):
    """Synchronous agent loop."""

    def __init__(self, agent: "Agent", loop: AbstractEventLoop = None):
        """
        Init agent loop.

        :param agent: AEA instance
        :param loop: asyncio loop to use. optional
        """
        super().__init__(agent=agent, loop=loop)
        self._agent: "AEA" = self._agent
        asyncio.set_event_loop(self._loop)

    async def _agent_loop(self) -> None:
        """Run loop inside coroutine but call synchronous callbacks from agent."""
        while self.is_running:
            self._spin_main_loop()
            await asyncio.sleep(self._agent.timeout)

    def _spin_main_loop(self) -> None:
        """Run one spin of agent loop: act, react, update."""
        self._agent.act()
        self._agent.react()
        self._agent.update()

    def _set_tasks(self) -> None:
        """Set run loop tasks."""
        self._tasks = [self._loop.create_task(self._agent_loop())]

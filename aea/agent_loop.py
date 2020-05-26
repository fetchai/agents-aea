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
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from enum import Enum
from functools import partial
from typing import (
    Callable,
    Dict,
    List,
)

from aea.exceptions import AEAException
from aea.helpers.async_utils import (
    AsyncState,
    PeriodicCaller,
    create_task,
    ensure_loop,
    wait_and_cancel,
)
from aea.mail.base import InBox
from aea.skills.base import Behaviour


logger = logging.getLogger(__file__)

if False:  # MYPY compatible for types definitions
    from aea.aea import AEA  # pragma: no cover
    from aea.agent import Agent  # pragma: no cover


class BaseAgentLoop(ABC):
    """Base abstract  agent loop class."""

    def __init__(self, agent: "Agent") -> None:
        """Init loop.

        :params agent: Agent or AEA to run.
        """
        self._agent = agent

    @abstractmethod
    def start(self) -> None:
        """Start agent loop."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stop agent loop."""
        raise NotImplementedError


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
        super().__init__(agent)
        self._agent: "AEA" = self._agent

        self._loop: AbstractEventLoop = ensure_loop(loop)

        self._behaviours_registry: Dict[Behaviour, PeriodicCaller] = {}
        self._state: AsyncState = AsyncState()
        self._exceptions: List[Exception] = []

    def start(self):
        """Start agent loop."""
        self._state.state = AgentLoopStates.started
        self._loop.run_until_complete(self._run())

    def stop(self):
        """Stop agent loop."""
        self._state.state = AgentLoopStates.stopping

    def _behaviour_exception_callback(self, fn: Callable, exc: Exception) -> None:
        """
        Call on behaviour's act exception.

        :param fn: behaviour's act
        :param: exc: Exception  raised

        :return: None
        """
        logger.exception(f"Loop: Exception: `{exc}` occured during `{fn}` processing")
        self._exceptions.append(exc)
        self._state.state = AgentLoopStates.error

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
            partial(self._agent._execution_control, behaviour.act_wrapper, behaviour),
            behaviour._tick_interval,
            behaviour._start_at,
            self._behaviour_exception_callback,
            self._loop,
        )
        self._behaviours_registry[behaviour] = periodic_caller
        periodic_caller.start()

    def _register_all_behaviours(self) -> None:
        """Register all AEA behaviours to run periodically."""
        for behaviour in self._agent._get_active_behaviours():
            self._register_behaviour(behaviour)

    def _unregister_behaviour(self, behaviour: Behaviour) -> None:
        """
        Unregister periodic execution of the behaviour.

        :param behaviour: Behaviour to schedule periodic execution.
        :return: None
        """
        periodic_caller = self._behaviours_registry.pop(behaviour, None)
        if periodic_caller is None:
            return
        periodic_caller.stop()

    def _stop_all_behaviours(self) -> None:
        """Unregister periodic execution of all registered behaviours."""
        for behaviour in list(self._behaviours_registry.keys()):
            self._unregister_behaviour(behaviour)

    async def _task_wait_for_stop(self) -> None:
        """Wait for stop and unregister all behaviours on exit."""
        try:
            await self._state.wait([AgentLoopStates.stopping, AgentLoopStates.error])
        finally:
            # stop all behaviours on cancel or stop
            self._stop_all_behaviours()

    async def _run(self) -> None:
        """Run all tasks and wait for stopping state."""
        tasks = self._create_tasks()

        exceptions = await wait_and_cancel(tasks)
        self._exceptions.extend(exceptions)

        if self._exceptions:
            # check exception raised during run
            self._handle_exceptions()

        self._state.state = AgentLoopStates.stopped

    def _handle_exceptions(self) -> None:
        """Log and raise exception if occurs."""
        if not self._exceptions:
            return

        for e in self._exceptions:
            logger.exception(e)

        raise self._exceptions[0]

    def _create_tasks(self) -> List[Task]:
        """
        Create tasks.

        :return: list of asyncio Tasks
        """
        tasks = [
            self._task_process_inbox(),
            self._task_process_internal_messages(),
            self._task_process_new_behaviours(),
            self._task_wait_for_stop(),
        ]
        return list(map(create_task, tasks))

    @property
    def is_running(self) -> bool:
        """Get running state of the loop."""
        return self._state.state == AgentLoopStates.started

    async def _task_process_inbox(self) -> None:
        """Process incoming messages."""
        inbox: InBox = self._agent._inbox
        while self.is_running:
            await inbox.async_wait()

            if not self.is_running:  # make it close faster
                return

            self._agent.react()

    async def _task_process_internal_messages(self) -> None:
        """Process decision maker's internal messages."""
        queue = self._agent.decision_maker.message_out_queue
        while self.is_running:
            msg = await queue.async_get()
            # TODO: better interaction with agent's internal messages
            self._agent._filter._process_internal_message(msg)  # type: ignore # mypy can not determine type of _filter

    async def _task_process_new_behaviours(self) -> None:
        """Process new behaviours added to skills in runtime."""
        while self.is_running:
            # TODO: better handling internal messages for skills internal updates
            self._agent._filter._handle_new_behaviours()  # type: ignore # mypy can not determine type of _filter
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
        super().__init__(agent)
        self._agent: "AEA" = self._agent

        try:
            self._loop = loop or asyncio.get_event_loop()
            assert not self._loop.is_closed()
            assert not self._loop.is_running()
        except (RuntimeError, AssertionError):
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        self.is_running = False

    def start(self) -> None:
        """Start agent loop."""
        self.is_running = True
        self._loop.run_until_complete(self._run())

    async def _run(self) -> None:
        """Run loop inside coroutine but call synchronous callbacks from agent."""
        while self.is_running:
            self._spin_main_loop()
            await asyncio.sleep(self._agent._timeout)

    def _spin_main_loop(self):
        """Run one spin of agent loop: act, react, update."""
        self._agent.act()
        self._agent.react()
        self._agent.update()

    def stop(self):
        """Stop agent loop."""
        self.is_running = False

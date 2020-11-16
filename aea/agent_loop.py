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
import datetime
from abc import ABC, abstractmethod
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from contextlib import suppress
from enum import Enum
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from aea.abstract_agent import AbstractAgent
from aea.exceptions import AEAException
from aea.helpers.async_utils import (
    AsyncState,
    HandlerItemGetter,
    PeriodicCaller,
    Runnable,
)
from aea.helpers.exec_timeout import ExecTimeoutThreadGuard, TimeoutException
from aea.helpers.logging import WithLogger, get_logger


class AgentLoopException(AEAException):
    """Exception for agent loop runtime errors."""


class AgentLoopStates(Enum):
    """Internal agent loop states."""

    initial = None
    started = "started"
    starting = "starting"
    stopped = "stopped"
    stopping = "stopping"
    error = "error"


class BaseAgentLoop(Runnable, WithLogger, ABC):
    """Base abstract  agent loop class."""

    def __init__(
        self,
        agent: AbstractAgent,
        loop: Optional[AbstractEventLoop] = None,
        threaded=False,
    ) -> None:
        """Init loop.

        :params agent: Agent or AEA to run.
        :params loop: optional asyncio event loop. if not specified a new loop will be created.
        """
        logger = get_logger(__name__, agent.name)
        WithLogger.__init__(self, logger)
        Runnable.__init__(self, loop=loop, threaded=threaded)

        self._agent: AbstractAgent = agent
        self._tasks: List[asyncio.Task] = []
        self._state: AsyncState = AsyncState(AgentLoopStates.initial)
        self._exceptions: List[Exception] = []

    @property
    def agent(self) -> AbstractAgent:  # pragma: nocover
        """Get agent."""
        return self._agent

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """Set event loop and all event loopp related objects."""
        self._loop: AbstractEventLoop = loop

    def _setup(self) -> None:  # pylint: disable=no-self-use
        """Set up loop before started."""
        # start and stop methods are classmethods cause one instance shared across muiltiple threads
        ExecTimeoutThreadGuard.start()

    def _teardown(self):  # pylint: disable=no-self-use
        """Tear down loop on stop."""
        # start and stop methods are classmethods cause one instance shared across muiltiple threads
        ExecTimeoutThreadGuard.stop()

    async def run(self) -> None:
        """Run agent loop."""
        self.logger.debug("agent loop started")
        self._state.set(AgentLoopStates.starting)
        self._setup()
        self._set_tasks()
        try:
            await self._gather_tasks()
        except (CancelledError, KeyboardInterrupt):
            pass
        finally:
            await self._stop()

    async def _stop(self) -> None:
        """Stop and cleanup."""
        self._teardown()
        self._stop_tasks()
        for t in self._tasks:
            with suppress(BaseException):
                await t
        self._state.set(AgentLoopStates.stopped)
        self.logger.debug("agent loop stopped")

    async def _gather_tasks(self) -> None:
        """Wait till first task exception."""
        await asyncio.gather(*self._tasks, loop=self._loop)

    @abstractmethod
    def _set_tasks(self) -> None:  # pragma: nocover
        """Set run loop tasks."""
        raise NotImplementedError

    def _stop_tasks(self) -> None:
        """Cancel all tasks."""
        for task in self._tasks:
            if task.done():
                continue  #  pragma: nocover
            task.cancel()

    @property
    def state(self) -> AgentLoopStates:
        """Get current main loop state."""
        return self._state.get()

    @property
    def is_running(self) -> bool:
        """Get running state of the loop."""
        return self._state.get() == AgentLoopStates.started


class AsyncAgentLoop(BaseAgentLoop):
    """Asyncio based agent loop suitable only for AEA."""

    NEW_BEHAVIOURS_PROCESS_SLEEP = 1  # check new behaviours registered every second.

    def __init__(
        self, agent: AbstractAgent, loop: AbstractEventLoop = None, threaded=False
    ):
        """
        Init agent loop.

        :param agent: AEA instance
        :param loop: asyncio loop to use. optional
        """
        super().__init__(agent=agent, loop=loop, threaded=threaded)
        self._agent: AbstractAgent = self._agent

        self._periodic_tasks: Dict[Callable, PeriodicCaller] = {}

    def _periodic_task_exception_callback(  # pylint: disable=unused-argument
        self, task_callable: Callable, exc: Exception
    ) -> None:
        """
        Call on periodic task exception.

        :param task_callable: function to be called
        :param: exc: Exception  raised

        :return: None
        """
        self._exceptions.append(exc)

    def _execution_control(
        self,
        fn: Callable,
        args: Optional[Sequence] = None,
        kwargs: Optional[Dict] = None,
    ) -> Any:
        """
        Execute skill function in exception handling environment.

        Logs error, stop agent or propagate exception depends on policy defined.

        :param fn: function to call
        :param args: optional sequence of arguments to pass to function on call
        :param kwargs: optional dict of keyword arguments to pass to function on call

        :return: same as function
        """
        execution_timeout = getattr(self.agent, "_execution_timeout", 0)

        try:
            with ExecTimeoutThreadGuard(execution_timeout):
                return fn(*(args or []), **(kwargs or {}))
        except TimeoutException:  # pragma: nocover
            self.logger.warning(
                "`{}` was terminated as its execution exceeded the timeout of {} seconds. Please refactor your code!".format(
                    fn, execution_timeout
                )
            )
        except Exception as e:  # pylint: disable=broad-except
            try:
                if self.agent.exception_handler(e, fn) is True:
                    self._state.set(AgentLoopStates.error)
                    raise
            except Exception as e:
                self._state.set(AgentLoopStates.error)
                self._exceptions.append(e)
                raise

    def _register_periodic_task(
        self,
        task_callable: Callable,
        period: float,
        start_at: Optional[datetime.datetime],
    ) -> None:
        """
        Register function to run periodically.

        :param task_callable: function to be called
        :param pediod: float: in seconds
        :param start_at: optional datetime, when to run task for the first time, otherwise call it right now

        :return: None
        """
        if task_callable in self._periodic_tasks:  # pragma: nocover
            # already registered
            return

        periodic_caller = PeriodicCaller(
            partial(self._execution_control, task_callable),
            period=period,
            start_at=start_at,
            exception_callback=self._periodic_task_exception_callback,
            loop=self._loop,
        )
        self._periodic_tasks[task_callable] = periodic_caller
        periodic_caller.start()
        self.logger.debug(f"Periodic task {task_callable} registered.")

    def _register_periodic_tasks(self) -> None:
        """Register all AEA related periodic tasks."""
        for (
            task_callable,
            (period, start_at),
        ) in self._agent.get_periodic_tasks().items():
            self._register_periodic_task(task_callable, period, start_at)

    def _unregister_periodic_task(self, task_callable: Callable) -> None:
        """
        Unregister periodic execution of the task.

        :param task_callable: function to be called periodically.
        :return: None
        """
        periodic_caller = self._periodic_tasks.pop(task_callable, None)
        if periodic_caller is None:  # pragma: nocover
            return
        periodic_caller.stop()

    def _stop_all_behaviours(self) -> None:
        """Unregister periodic execution of all registered behaviours."""
        for task_callable in list(self._periodic_tasks.keys()):
            self._unregister_periodic_task(task_callable)

    async def _task_wait_for_error(self) -> None:
        """Wait for error and raise first."""
        await self._state.wait(AgentLoopStates.error)
        raise self._exceptions[0]

    def _stop_tasks(self) -> None:
        """Cancel all tasks and stop behaviours registered."""
        BaseAgentLoop._stop_tasks(self)
        self._stop_all_behaviours()

    def _set_tasks(self) -> None:
        """Set run loop tasks."""
        self._tasks = self._create_tasks()
        self.logger.debug("tasks created!")

    def _create_tasks(self) -> List[Task]:
        """
        Create tasks.

        :return: list of asyncio Tasks
        """
        tasks = [
            self._process_messages(HandlerItemGetter(self._message_handlers())),
            self._task_register_periodic_tasks(),
            self._task_wait_for_error(),
        ]
        return list(map(self._loop.create_task, tasks))  # type: ignore  # some issue with map and create_task

    def _message_handlers(self) -> List[Tuple[Callable[[Any], None], Callable]]:
        """Get all agent's message handlers."""
        return self._agent.get_message_handlers()

    async def _process_messages(self, getter: HandlerItemGetter) -> None:
        """Process message from ItemGetter."""
        self.logger.info("Start processing messages...")
        self._state.set(AgentLoopStates.started)
        while self.is_running:
            handler, item = await getter.get()
            self._execution_control(handler, [item])

    async def _task_register_periodic_tasks(self) -> None:
        """Process new behaviours added to skills in runtime."""
        while self.is_running:
            self._register_periodic_tasks()  # re register, cause new may appear
            await asyncio.sleep(self.NEW_BEHAVIOURS_PROCESS_SLEEP)


SyncAgentLoop = AsyncAgentLoop  # temporary solution!

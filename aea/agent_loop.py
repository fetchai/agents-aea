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
import logging
import time
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop, TimerHandle
from asyncio.futures import Future
from asyncio.tasks import ALL_COMPLETED, FIRST_COMPLETED, Task
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

from aea.mail.base import InBox
from aea.skills.base import Behaviour


try:
    from asyncio import create_task
except ImportError:
    # for python3.6!
    from asyncio import ensure_future as create_task  # type: ignore


logger = logging.getLogger(__file__)

if False:  # MYPY compatible for types definitions
    from aea.aea import AEA
    from aea.agent import Agent


def ensure_list(value: Any) -> List:
    """Return [value] or value if value is a list."""
    if not isinstance(value, list):
        value = [value]
    return value


class AsyncState:
    """Awaitable state."""

    def __init__(self, initial_state: Any = None, loop: AbstractEventLoop = None):
        """Init async state.

        :param initial_state: state to set on start.
        :param loop: optional asyncio event loop.
        """
        self._state = initial_state
        self._watchers: Set[Future] = set()
        self._loop = loop or asyncio.get_event_loop()

    @property
    def state(self) -> Any:
        """Return current state."""
        return self._state

    def set(self, state: Any) -> None:
        """Set state."""
        if self._state == state:
            return
        self._state_changed(state)
        self._state = state

    def _state_changed(self, state: Any) -> None:
        """Fulfill watchers for state."""
        for watcher in list(self._watchers):
            if state in watcher._states:  # type: ignore
                self._loop.call_soon_threadsafe(
                    watcher.set_result, (self._state, state)
                )

    async def wait(self, state_or_states: Union[Any, List[Any]]) -> Tuple[Any, Any]:
        """Wait state to be set.

        :params state_or_states: state or list of states.
        :return: tuple of previous state and new state.
        """
        states = ensure_list(state_or_states)

        if self._state in states:
            return (None, self._state)

        watcher: Future = Future()
        watcher._states = states  # type: ignore
        self._watchers.add(watcher)
        try:
            return await watcher
        finally:
            self._watchers.remove(watcher)


class PeriodicCaller:
    """Schedule a periodic call of callable using event loop."""

    def __init__(
        self,
        callback: Callable,
        period: float,
        start_at: Optional[datetime.datetime] = None,
        exception_callback: Optional[Callable] = None,
        loop: Optional[AbstractEventLoop] = None,
    ):
        """
        Init periodic caller.

        :param callback: function to call periodically
        :param period: period in seconds.
        :param start_at: optional first call datetime
        :param exception_callback: optional handler to call on exception raised.
        :param loop: optional asyncio event loop
        """
        self._loop = loop or asyncio.get_event_loop()
        self._periodic_callable = callback
        self._start_at = start_at or datetime.datetime.now()
        self._period = period
        self._timerhandle: Optional[TimerHandle] = None
        self._exception_callback = exception_callback

    def _callback(self) -> None:
        """Call on each schduled call."""
        self._schedule_call()
        try:
            self._periodic_callable()
        except Exception as exception:
            if not self._exception_callback:
                raise
            self._exception_callback(self._periodic_callable, exception)

    def _schedule_call(self) -> None:
        """Set schedule for call."""
        if self._period is None:
            return

        if self._timerhandle is None:
            ts = time.mktime(self._start_at.timetuple())
            delay = max(0, ts - time.time())
            self._timerhandle = self._loop.call_later(delay, self._callback)
        else:
            self._timerhandle = self._loop.call_later(self._period, self._callback)

    def start(self) -> None:
        """Activate periodi calls."""
        if self._timerhandle:
            return
        self._schedule_call()

    def stop(self) -> None:
        """Remove from schedule."""
        if not self._timerhandle:
            return

        self._timerhandle.cancel()
        self._timerhandle = None


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


class AgentLoopException(Exception):
    """Exception for agent loop runtime errors."""


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

        try:
            self._loop = loop or asyncio.get_event_loop()
            assert not self._loop.is_closed()
            assert not self._loop.is_running()
        except (RuntimeError, AssertionError):
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        self._behaviours_registry: Dict[Behaviour, PeriodicCaller] = {}
        self._state: AsyncState = AsyncState()
        self._exceptions: List[Exception] = []

    def start(self):
        """Start agent loop."""
        self._state.set("started")
        self._loop.run_until_complete(self._run())

    def stop(self):
        """Stop agent loop."""
        self._state.set("stopping")

    def _behaviour_exception_callback(self, fn: Callable, exc: Exception) -> None:
        """
        Call on behaviour's act exception.

        :param fn: behaviour's act
        :param: exc: Exception  raised

        :return: None
        """
        logger.exception(f"Exception: `{exc}` occured during `{fn}` processing")
        self._exceptions.append(exc)
        self._state.set("error")

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
            behaviour.act,
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
        for periodic_caller in self._behaviours_registry.values():
            periodic_caller.stop()
        self._behaviours_registry = {}

    def _create_tasks(self):
        """Create tasks to execute and wait."""
        tasks = self._create_processing_tasks()
        stopping_task = create_task(self._state.wait(["stopping", "error"]))

        tasks.append(stopping_task)
        return tasks

    async def _cancel_and_wait_tasks(self, tasks: List[Task]) -> None:
        """Cancel all tasks and wait they completed."""
        for t in tasks:
            t.cancel()

        await asyncio.wait(tasks, return_when=ALL_COMPLETED)

        for t in tasks:
            if t.cancelled():
                continue
            exc = t.exception()
            if exc:
                self._exceptions.append(cast(Exception, exc))

    async def _run(self) -> None:
        """Run all tasks and wait for stopping state."""
        tasks = self._create_tasks()

        await asyncio.wait(tasks, return_when=FIRST_COMPLETED)

        # one task completed by some reason: error or state == stopped.
        # clean up
        self._stop_all_behaviours()
        await self._cancel_and_wait_tasks(tasks)

        if self._exceptions:
            # check exception raised during run
            raise AgentLoopException(self._exceptions)

        self._state.set("stopped")

    def _create_processing_tasks(self) -> List[Task]:
        """
        Create processing tasks.

        :return: list of asyncio Tasks
        """
        tasks = [
            self._task_process_inbox(),
            self._task_process_internal_messages(),
            self._task_process_new_behaviours(),
        ]
        return list(map(create_task, tasks))

    @property
    def is_running(self) -> bool:
        """Get running state of the loop."""
        return self._state.state == "started"

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

    def __init__(self, agent: "Agent") -> None:
        """
        Init agent loop.

        :param agent: agent or AEA instance.
        """
        super().__init__(agent)
        self.is_running = False

    def start(self) -> None:
        """Start agent loop."""
        self.is_running = True
        while self.is_running:
            self._spin_main_loop()
            time.sleep(self._agent._timeout)

    def _spin_main_loop(self):
        """Run one spin of agent loop: act, react, update."""
        self._agent.act()
        self._agent.react()
        self._agent.update()

    def stop(self):
        """Stop agent loop."""
        self.is_running = False

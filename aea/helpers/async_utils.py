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
"""This module contains the misc utils for async code."""
import asyncio
import datetime
import time
from asyncio.events import AbstractEventLoop, TimerHandle
from asyncio.futures import Future
from asyncio.tasks import ALL_COMPLETED, FIRST_COMPLETED, Task
from typing import Any, Callable, List, Optional, Sequence, Set, Tuple, Union, cast

try:
    from asyncio import create_task
except ImportError:  # pragma: no cover
    # for python3.6!
    from asyncio import ensure_future as create_task  # type: ignore # noqa: F401


def ensure_list(value: Any) -> List:
    """Return [value] or list(value) if value is a sequence."""
    if not isinstance(value, (list, tuple)):
        value = [value]
    return list(value)


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

    @state.setter
    def state(self, state: Any) -> None:
        """Set state."""
        if self._state == state:  # pragma: no cover
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

    async def wait(self, state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]:
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
        exception_callback: Optional[Callable[[Callable, Exception], None]] = None,
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
        """Call on each scheduled call."""
        self._schedule_call()
        try:
            self._periodic_callable()
        except Exception as exception:
            if not self._exception_callback:
                raise
            self._exception_callback(self._periodic_callable, exception)

    def _schedule_call(self) -> None:
        """Set schedule for call."""
        if self._timerhandle is None:
            ts = time.mktime(self._start_at.timetuple())
            delay = max(0, ts - time.time())
            self._timerhandle = self._loop.call_later(delay, self._callback)
        else:
            self._timerhandle = self._loop.call_later(self._period, self._callback)

    def start(self) -> None:
        """Activate period calls."""
        if self._timerhandle:
            return
        self._schedule_call()

    def stop(self) -> None:
        """Remove from schedule."""
        if not self._timerhandle:
            return

        self._timerhandle.cancel()
        self._timerhandle = None


def ensure_loop(loop: AbstractEventLoop = None) -> AbstractEventLoop:
    """Use loop provided or create new if not provided or closed."""
    try:
        loop = loop or asyncio.get_event_loop()
        assert not loop.is_closed()
        assert not loop.is_running()
    except (RuntimeError, AssertionError):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def wait_and_cancel(
    tasks: Sequence[Task],
    include_cancelled: bool = False,
    loop: Optional[AbstractEventLoop] = None,
) -> List[Exception]:
    """
    Wait first task completed or exception raised and cancel other tasks.

    :param tasks: list of tasks to run and wait.

    :return: list of exceptions raised.
    """
    exceptions: List[Exception] = []

    _, pending = await asyncio.wait(tasks, return_when=FIRST_COMPLETED)

    for task in pending:
        task.cancel()

    completed, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)

    assert not pending

    for task in completed:
        if not include_cancelled and task.cancelled():
            continue
        exc = task.exception()
        if exc:
            exceptions.append(cast(Exception, exc))

    return exceptions

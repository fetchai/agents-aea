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
import collections
import datetime
import logging
import subprocess  # nosec
import time
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop, TimerHandle
from asyncio.futures import Future
from asyncio.tasks import FIRST_COMPLETED, Task
from collections.abc import Iterable
from contextlib import contextmanager, suppress
from threading import Thread
from typing import (
    Any,
    Awaitable,
    Callable,
    Container,
    Generator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

try:
    from asyncio import create_task  # pylint: disable=ungrouped-imports,unused-import
except ImportError:  # pragma: no cover
    # for python3.6!
    from asyncio import ensure_future as create_task  # type: ignore # noqa: F401 # pylint: disable=ungrouped-imports,unused-import


logger = logging.getLogger(__file__)


def ensure_list(value: Any) -> List:
    """Return [value] or list(value) if value is a sequence."""
    if isinstance(value, list):
        return value

    if isinstance(value, Iterable):
        return list(value)

    return [value]


not_set = object()


class AsyncState:
    """Awaitable state."""

    def __init__(
        self, initial_state: Any = None, states_enum: Optional[Container[Any]] = None
    ):
        """Init async state.

        :param initial_state: state to set on start.
        :param states_enum: container of valid states if not provided state not checked on set.
        """
        self._state = initial_state
        self._watchers: Set[Future] = set()
        self._callbacks: List[Callable[[Any], None]] = []
        self._states_enum = states_enum

    def set(self, state: Any) -> None:
        """Set state."""
        if self._states_enum is not None and state not in self._states_enum:
            raise ValueError(
                f"Unsupported state: {state}. Valid states are {self._states_enum}"
            )

        if self._state == state:  # pragma: no cover
            return

        self._state_changed(state)
        self._state = state

    def add_callback(self, callback_fn: Callable[[Any], None]) -> None:
        """
        Add callback to track state changes.

        :param callback_fn: callable object to be called on state changed.

        :return: None
        """
        self._callbacks.append(callback_fn)

    def get(self) -> Any:
        """Get state."""
        return self._state

    def _state_changed(self, state: Any) -> None:
        """Fulfill watchers for state."""
        for callback_fn in self._callbacks:
            try:
                callback_fn(state)
            except Exception:  # pylint: disable=broad-except
                logger.exception(f"Exception on calling {callback_fn}")

        for watcher in list(self._watchers):
            if state not in watcher._states:  # type: ignore # pylint: disable=protected-access  # pragma: nocover
                continue
            if not watcher.done():
                watcher._loop.call_soon_threadsafe(  # pylint: disable=protected-access
                    self._watcher_result_callback(watcher), (self._state, state)
                )
            self._remove_watcher(watcher)

    def _remove_watcher(self, watcher: Future) -> None:
        """Remove watcher for state wait."""
        try:
            self._watchers.remove(watcher)
        except KeyError:
            pass

    @staticmethod
    def _watcher_result_callback(watcher: Future) -> Callable:
        """Create callback for watcher result."""
        # docstyle.
        def _callback(result):
            if watcher.done():  # pragma: nocover
                return
            watcher.set_result(result)

        return _callback

    async def wait(self, state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]:
        """Wait state to be set.

        :params state_or_states: state or list of states.
        :return: tuple of previous state and new state.
        """
        states = ensure_list(state_or_states)

        if self._state in states:
            return (None, self._state)

        watcher: Future = Future()
        watcher._states = states  # type: ignore  # pylint: disable=protected-access
        self._watchers.add(watcher)
        try:
            return await watcher
        finally:
            self._remove_watcher(watcher)

    @contextmanager
    def transit(
        self, initial: Any = not_set, success: Any = not_set, fail: Any = not_set
    ) -> Generator:
        """
        Change state context according to success or not.

        :param initial: set state on context enter, not_set by default
        :param success: set state on context block done, not_set by default
        :param fail: set state on context block raises exception, not_set by default

        :return: None
        """
        try:
            if initial is not not_set:
                self.set(initial)
            yield
            if success is not not_set:
                self.set(success)
        except BaseException:
            if fail is not not_set:
                self.set(fail)
            raise


class PeriodicCaller:
    """
    Schedule a periodic call of callable using event loop.

    Used for periodic function run using asyncio.
    """

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
        except Exception as exception:  # pylint: disable=broad-except
            if not self._exception_callback:  # pragma: nocover
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
        if self._timerhandle:  # pragma: nocover
            return

        self._schedule_call()

    def stop(self) -> None:
        """Remove from schedule."""
        if not self._timerhandle:  # pragma: nocover
            return

        self._timerhandle.cancel()
        self._timerhandle = None


def ensure_loop(loop: Optional[AbstractEventLoop] = None) -> AbstractEventLoop:
    """
    Use loop provided or create new if not provided or closed.

    Return loop passed if its provided,not closed and not running, otherwise returns new event loop.

    :param loop: optional event loop
    :return: asyncio event loop
    """
    try:
        loop = loop or asyncio.new_event_loop()
        if loop.is_closed():
            raise ValueError("Event loop closed.")  # pragma: nocover
        if loop.is_running():
            raise ValueError("Event loop running.")
    except (RuntimeError, ValueError):
        loop = asyncio.new_event_loop()

    return loop


class AnotherThreadTask:
    """
    Schedule a task to run on the loop in another thread.

    Provides better cancel behaviour: on cancel it will wait till cancelled completely.
    """

    def __init__(self, coro: Awaitable, loop: AbstractEventLoop) -> None:
        """
        Init the task.

        :param coro: coroutine to schedule
        :param loop: an event loop to schedule on.
        """
        self._loop = loop
        self._coro = coro
        self._task: Optional[asyncio.Task] = None
        self._future = asyncio.run_coroutine_threadsafe(self._get_task_result(), loop)

    async def _get_task_result(self) -> Any:
        """
        Get task result, should be run in target loop.

        :return: task result value or raise an exception if task failed
        """
        self._task = self._loop.create_task(self._coro)
        return await self._task

    def result(self, timeout: Optional[float] = None) -> Any:
        """
        Wait for coroutine execution result.

        :param timeout: optional timeout to wait in seconds.
        """
        return self._future.result(timeout)

    def cancel(self) -> None:
        """Cancel coroutine task execution in a target loop."""
        if self._task is None:
            self._loop.call_soon_threadsafe(self._future.cancel)
        else:
            self._loop.call_soon_threadsafe(self._task.cancel)

    def done(self) -> bool:
        """Check task is done."""
        return self._future.done()


class ThreadedAsyncRunner(Thread):
    """Util to run thread with event loop and execute coroutines inside."""

    def __init__(self, loop=None) -> None:
        """
        Init threaded runner.

        :param loop: optional event loop. is it's running loop, threaded runner will use it.
        """
        self._loop = loop or asyncio.new_event_loop()
        if self._loop.is_closed():
            raise ValueError("Event loop closed.")  # pragma: nocover
        super().__init__(daemon=True)

    def start(self) -> None:
        """Start event loop in dedicated thread."""
        if self.is_alive() or self._loop.is_running():  # pragma: nocover
            return
        super().start()
        self.call(asyncio.sleep(0.001)).result(1)

    def run(self) -> None:
        """Run code inside thread."""
        logger.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        logger.debug("Asyncio loop has been stopped.")

    def call(self, coro: Awaitable) -> Any:
        """
        Run a coroutine inside the event loop.

        :param coro: a coroutine to run.
        """
        return AnotherThreadTask(coro, self._loop)

    def stop(self) -> None:
        """Stop event loop in thread."""
        logger.debug("Stopping...")

        if not self.is_alive():  # pragma: nocover
            return

        if self._loop.is_running():
            logger.debug("Stopping loop...")
            self._loop.call_soon_threadsafe(self._loop.stop)

        logger.debug("Wait thread to join...")
        self.join(10)
        logger.debug("Stopped.")


async def cancel_and_wait(task: Optional[Task]) -> Any:
    """Wait cancelled task and skip CancelledError."""
    if not task:  # pragma: nocover
        return
    try:
        if task.done():
            return await task

        task.cancel()
        return await task
    except CancelledError as e:
        return e


class AwaitableProc:
    """
    Async-friendly subprocess.Popen
    """

    def __init__(self, *args, **kwargs):
        """Initialise awaitable proc."""
        self.args = args
        self.kwargs = kwargs
        self.proc = None
        self._thread = None
        self.loop = None
        self.future = None

    async def start(self):
        """Start the subprocess"""
        self.proc = subprocess.Popen(*self.args, **self.kwargs)  # nosec
        self.loop = asyncio.get_event_loop()
        self.future = asyncio.futures.Future()
        self._thread = Thread(target=self._in_thread)
        self._thread.start()
        try:
            return await asyncio.shield(self.future)
        except asyncio.CancelledError:  # pragma: nocover
            self.proc.terminate()
            return await self.future
        finally:
            self._thread.join()

    def _in_thread(self):
        self.proc.wait()
        self.loop.call_soon_threadsafe(self.future.set_result, self.proc.returncode)


class ItemGetter:
    """Virtual queue like object to get items from getters function."""

    def __init__(self, getters: List[Callable]) -> None:
        """
        Init ItemGetter.

        :param getters: List of couroutines to be awaited.
        """
        if not getters:  # pragma: nocover
            raise ValueError("getters list can not be empty!")
        self._getters = getters
        self._items: collections.deque = collections.deque()

    async def get(self) -> Any:
        """Get item."""
        if not self._items:
            await self._wait()
        return self._items.pop()

    async def _wait(self) -> None:
        """Populate cache queue with items."""
        loop = asyncio.get_event_loop()
        try:
            tasks = [loop.create_task(getter()) for getter in self._getters]
            done, _ = await asyncio.wait(tasks, return_when=FIRST_COMPLETED)
            for task in done:
                self._items.append(await task)
        finally:
            for task in tasks:
                if task.done():
                    continue
                task.cancel()
                with suppress(CancelledError):
                    await task


class HandlerItemGetter(ItemGetter):
    """ItemGetter with handler passed."""

    @staticmethod
    def _make_getter(handler: Callable[[Any], None], getter: Callable) -> Callable:
        """
        Create getter for handler and item getter function.

        :param handler: callable with one position argument.
        :param getter: a couroutine to await for item

        :return: callable to return handler and item from getter.
        """
        # for pydocstyle
        async def _getter():
            return handler, await getter()

        return _getter

    def __init__(self, getters: List[Tuple[Callable[[Any], None], Callable]]):
        """
        Init HandlerItemGetter.

        :param getters: List of tuples of handler and couroutine to be awaiteed for an item.
        """
        super(HandlerItemGetter, self).__init__(
            [self._make_getter(handler, getter) for handler, getter in getters]
        )

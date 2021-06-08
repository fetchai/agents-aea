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
import logging
import time
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop, TimerHandle
from asyncio.futures import Future
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
    from asyncio import (  # type: ignore # noqa: F401 # pylint: disable=ungrouped-imports,unused-import
        ensure_future as create_task,
    )


_default_logger = logging.getLogger(__file__)


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
    ) -> None:
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
                _default_logger.exception(f"Exception on calling {callback_fn}")

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
        def _callback(result: Any) -> None:
            if watcher.done():  # pragma: nocover
                return
            watcher.set_result(result)

        return _callback

    async def wait(self, state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]:
        """Wait state to be set.

        :param state_or_states: state or list of states.

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
        :yield: generator
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
    ) -> None:
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
            self.stop()
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
        :return: result
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

    def __init__(self, loop: Optional[AbstractEventLoop] = None) -> None:
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
        _default_logger.debug("Starting threaded asyncio loop...")
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        _default_logger.debug("Asyncio loop has been stopped.")

    def call(self, coro: Awaitable) -> Any:
        """
        Run a coroutine inside the event loop.

        :param coro: a coroutine to run.
        :return: task
        """
        return AnotherThreadTask(coro, self._loop)

    def stop(self) -> None:
        """Stop event loop in thread."""
        _default_logger.debug("Stopping...")

        if not self.is_alive():  # pragma: nocover
            return

        if self._loop.is_running():
            _default_logger.debug("Stopping loop...")
            self._loop.call_soon_threadsafe(self._loop.stop)

        _default_logger.debug("Wait thread to join...")
        self.join(10)
        _default_logger.debug("Stopped.")


ready_future: Future = Future()
ready_future.set_result(None)


class Runnable(ABC):
    """
    Abstract Runnable class.

    Use to run async task in same event loop or in dedicated thread.
    Provides: start, stop sync methods to start and stop task
    Use wait_completed to await task was completed.
    """

    def __init__(
        self, loop: asyncio.AbstractEventLoop = None, threaded: bool = False
    ) -> None:
        """
        Init runnable.

        :param loop: asyncio event loop to use.
        :param threaded: bool. start in thread if True.
        """
        if loop and threaded:
            raise ValueError(
                "You can not set a loop in threaded mode. A dedicated loop will be created for each thread."
            )
        self._loop = loop
        self._threaded = threaded
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[Thread] = None
        self._completed_event: Optional[asyncio.Event] = None
        self._got_result = False
        self._was_cancelled = False
        self._is_running: bool = False
        self._stop_called = 0

    def start(self) -> bool:
        """
        Start runnable.

        :return: bool started or not.
        """
        if self._task and not self._task.done():
            _default_logger.debug(f"{self} already running")
            return False

        self._is_running = False
        self._got_result = False
        self._set_loop()
        self._completed_event = asyncio.Event(loop=self._loop)
        self._was_cancelled = False

        if self._stop_called > 0:
            # used in case of race when stop called before start!
            _default_logger.debug(f"{self} was already stopped before started!")
            self._stop_called = 0
            return True

        self._set_task()

        if self._threaded:
            self._thread = Thread(
                target=self._thread_target, name=self.__class__.__name__  # type: ignore # loop was set in set_loop
            )
            self._thread.setDaemon(True)
            self._thread.start()
        self._stop_called = 0
        return True

    def _thread_target(self) -> None:
        """Start event loop and task in the dedicated thread."""
        if not self._loop:
            raise ValueError("Call _set_loop() first!")  # pragma: nocover
        if not self._task:
            raise ValueError("Call _set_task() first!")  # pragma: nocover
        try:
            self._loop.run_until_complete(self._task)
        except BaseException:  # pylint: disable=broad-except)
            logging.exception(f"Exception raised in {self}")
        self._loop.stop()
        self._loop.close()

    def _set_loop(self) -> None:
        """Select and set loop."""
        if self._threaded:
            self._loop = asyncio.new_event_loop()
        else:
            try:
                self._loop = self._loop or asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

    def _set_task(self) -> None:
        """Create task."""
        if not self._loop:  # pragma: nocover
            raise ValueError("Loop was not set.")
        self._task = self._loop.create_task(self._run_wrapper())
        _default_logger.debug(f"{self} task set")

    async def _run_wrapper(self) -> None:
        """Wrap run() method."""
        if not self._completed_event or not self._loop:  # pragma: nocover
            raise ValueError("Start was not called!")
        self._is_running = True
        try:
            with suppress(asyncio.CancelledError):
                return await self.run()
        finally:
            self._loop.call_soon_threadsafe(self._completed_event.set)
            self._is_running = False

    @property
    def is_running(self) -> bool:  # pragma: nocover
        """Get running state."""
        return self._is_running

    @abstractmethod
    async def run(self) -> Any:
        """Implement run logic respectful to CancelError on termination."""

    def wait_completed(
        self, sync: bool = False, timeout: float = None, force_result: bool = False
    ) -> Awaitable:
        """
        Wait runnable execution completed.

        :param sync: bool. blocking wait
        :param timeout: float seconds
        :param force_result: check result even it was waited.

        :return: awaitable if sync is False, otherwise None
        """
        if not self._task:
            _default_logger.warning("Runnable is not started")
            return ready_future

        if self._got_result and not force_result:
            return ready_future

        if sync:
            self._wait_sync(timeout)
            return ready_future

        return self._wait_async(timeout)

    def _wait_sync(self, timeout: Optional[float] = None) -> None:
        """Wait task completed in sync manner."""
        if self._task is None or not self._loop:  # pragma: nocover
            raise ValueError("task is not set!")

        if self._threaded or self._loop.is_running():
            start_time = time.time()

            while not self._task.done():
                time.sleep(0.01)
                if timeout is not None and time.time() - start_time > timeout:
                    raise asyncio.TimeoutError()

            if self._thread:
                self._thread.join(timeout)

            self._got_result = True
            if self._task.exception():
                raise self._task.exception()
        else:
            self._loop.run_until_complete(
                asyncio.wait_for(self._wait(), timeout=timeout)
            )

    def _wait_async(self, timeout: Optional[float] = None) -> Awaitable:
        if not self._threaded:
            return asyncio.wait_for(self._wait(), timeout=timeout)

        if self._task is None:  # pragma: nocover
            raise ValueError("task is not set!")

        # for threaded mode create a future and bind it to task
        loop = asyncio.get_event_loop()
        fut = loop.create_future()

        def done(task: Future) -> None:
            try:
                if fut.done():  # pragma: nocover
                    return
                if task.exception():
                    fut.set_exception(task.exception())
                else:  # pragma: nocover
                    fut.set_result(None)
            finally:
                self._got_result = True

        if self._task.done():
            done(self._task)
        else:
            self._task.add_done_callback(
                lambda task: loop.call_soon_threadsafe(lambda: done(task))
            )

        return fut

    async def _wait(self) -> None:
        """Wait internal method."""
        if not self._task or not self._completed_event:  # pragma: nocover
            raise ValueError("Not started")

        await self._completed_event.wait()

        try:
            await self._task
        finally:
            self._got_result = True

    def stop(self, force: bool = False) -> None:
        """Stop runnable."""
        _default_logger.debug(f"{self} is going to be stopped {self._task}")
        if not self._task or not self._loop:  # pragma: nocover
            self._stop_called += 1
            return

        if self._task.done():
            return

        self._loop.call_soon_threadsafe(self._task_cancel, force)

    def _task_cancel(self, force: bool = False) -> None:
        """Cancel task internal method."""
        if self._task is None:
            return

        if self._was_cancelled and not force:
            return

        self._was_cancelled = True
        self._task.cancel()

    def start_and_wait_completed(self, *args: Any, **kwargs: Any) -> Awaitable:
        """Alias for start and wait methods."""
        self.start()
        return self.wait_completed(*args, **kwargs)

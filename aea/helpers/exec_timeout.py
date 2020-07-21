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
"""Python code execution time limit tools."""
import asyncio
import concurrent
import ctypes
import logging
import signal
import threading
from abc import ABC, abstractmethod
from asyncio import Future
from asyncio.events import AbstractEventLoop
from threading import Lock
from types import TracebackType
from typing import Optional, Type

logger = logging.getLogger(__file__)


class TimeoutResult:
    """Result of ExecTimeout context manager."""

    def __init__(self):
        """Init."""
        self._cancelled_by_timeout = False

    def set_cancelled_by_timeout(self) -> None:
        """
        Set code was terminated cause timeout.

        :return: None
        """
        self._cancelled_by_timeout = True

    def is_cancelled_by_timeout(self) -> bool:
        """
        Return True if code was terminated by ExecTimeout cause timeout.

        :return: bool
        """
        return self._cancelled_by_timeout


class TimeoutException(BaseException):
    """
    TimeoutException raised by ExecTimeout context managers in thread with limited execution time.

    Used internally, does not propagated outside of context manager
    """


class BaseExecTimeout(ABC):
    """
    Base class for implementing context managers to limit python code execution time.

    exception_class - is exception type to raise in code controlled in case of timeout.
    """

    exception_class: Type[BaseException] = TimeoutException

    def __init__(self, timeout: float = 0.0):
        """
        Init.

        :param timeout: number of seconds to execute code before interruption
        """
        self.timeout = timeout
        self.result = TimeoutResult()

    def _on_timeout(self, *args, **kwargs) -> None:
        """Raise exception on timeout."""
        raise self.exception_class()

    def __enter__(self) -> TimeoutResult:
        """
        Enter context manager.

        :return: TimeoutResult
        """
        if self.timeout:
            self._set_timeout_watch()

        return self.result

    def __exit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        """
        Exit context manager.

        :return: bool
        """
        if self.timeout:
            self._remove_timeout_watch()

        if isinstance(exc_val, TimeoutException):
            self.result.set_cancelled_by_timeout()

    @abstractmethod
    def _set_timeout_watch(self) -> None:
        """
        Start control over execution time.

        Should be implemented in concrete class.

        :return: None
        """
        raise NotImplementedError  # pragma: nocover

    @abstractmethod
    def _remove_timeout_watch(self) -> None:
        """
        Stop control over execution time.

        Should be implemented in concrete class.

        :return: None
        """
        raise NotImplementedError  # pragma: nocover


class ExecTimeoutSigAlarm(BaseExecTimeout):
    """
    ExecTimeout context manager implementation using signals and SIGALARM.

    Does not support threads, have to be used only in main thread.
    """

    def _set_timeout_watch(self) -> None:
        """
        Start control over execution time.

        :return: None
        """
        signal.setitimer(signal.ITIMER_REAL, self.timeout, 0)
        signal.signal(signal.SIGALRM, self._on_timeout)

    def _remove_timeout_watch(self):
        """
        Stop control over execution time.

        :return: None
        """
        signal.setitimer(signal.ITIMER_REAL, 0, 0)


class ExecTimeoutThreadGuard(BaseExecTimeout):
    """
    ExecTimeout context manager implementation using threads and PyThreadState_SetAsyncExc.

    Support threads.
    Requires supervisor thread start/stop to control execution time control.
    Possible will be not accurate in case of long c functions used inside code controlled.
    """

    _supervisor_thread: Optional[threading.Thread] = None
    _loop: Optional[AbstractEventLoop] = None
    _stopped_future: Optional[Future] = None
    _start_count: int = 0
    _lock: Lock = Lock()

    def __init__(self, timeout: float = 0.0):
        """
        Init ExecTimeoutThreadGuard variables.

        :param timeout: number of seconds to execute code before interruption
        """
        super().__init__(timeout=timeout)

        self._future_guard_task: Optional[concurrent.futures._base.Future[None]] = None
        self._thread_id: Optional[int] = None

    @classmethod
    def start(cls) -> None:
        """
        Start supervisor thread to check timeouts.

        Supervisor starts once but number of start counted.

        :return: None
        """
        with cls._lock:
            cls._start_count += 1

            if cls._supervisor_thread:  # pragma: nocover
                return

            cls._loop = asyncio.new_event_loop()
            cls._stopped_future = Future(loop=cls._loop)
            cls._supervisor_thread = threading.Thread(target=cls._supervisor_event_loop)
            cls._supervisor_thread.start()

    @classmethod
    def stop(cls, force: bool = False) -> None:
        """
        Stop supervisor thread.

        Actual stop performed on force == True or if  number of stops == number of starts

        :param force: force stop regardless number of start.
        :return: None
        """
        with cls._lock:
            if not cls._supervisor_thread:  # pragma: nocover
                return

            cls._start_count -= 1

            if cls._start_count <= 0 or force:
                cls._loop.call_soon_threadsafe(cls._stopped_future.set_result, True)  # type: ignore
                if cls._supervisor_thread and cls._supervisor_thread.is_alive():
                    cls._supervisor_thread.join()
                cls._supervisor_thread = None

    @classmethod
    def _supervisor_event_loop(cls) -> None:
        """Start supervisor thread to execute asyncio task controlling execution time."""
        # pydocstyle: noqa # cause black reformats with pydocstyle confilct
        async def wait_stopped() -> None:
            await cls._stopped_future  # type: ignore

        cls._loop.run_until_complete(wait_stopped())  # type: ignore

    async def _guard_task(self) -> None:
        """
        Task to terminate thread on timeout.

        :return: None
        """
        await asyncio.sleep(self.timeout)
        self._set_thread_exception(self._thread_id, self.exception_class)  # type: ignore

    @staticmethod
    def _set_thread_exception(thread_id: int, exception_class: Type[Exception]) -> None:
        """
        Terminate code execution in specific thread by setting exception.

        :return: None
        """
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(exception_class)
        )

    def _set_timeout_watch(self) -> None:
        """
        Start control over execution time.

        Set task checking code execution time.
        ExecTimeoutThreadGuard.start is required at least once in project before usage!

        :return: None
        """
        if not self._supervisor_thread:
            logger.warning(
                "ExecTimeoutThreadGuard is used but not started! No timeout wil be applied!"
            )
            return

        self._thread_id = threading.current_thread().ident
        self._future_guard_task = asyncio.run_coroutine_threadsafe(
            self._guard_task(), self._loop  # type: ignore
        )

    def _remove_timeout_watch(self) -> None:
        """
        Stop control over execution time.

        Cancel task checking code execution time.

        :return: None
        """
        if self._future_guard_task and not self._future_guard_task.done():
            self._future_guard_task.cancel()
            self._future_guard_task = None

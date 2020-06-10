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
"""This module contains the helpers to run multiple stoppable tasks in different modes: async, threaded, multiprocess ."""
import asyncio
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from asyncio.tasks import FIRST_EXCEPTION
from concurrent.futures._base import Executor
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from threading import Thread
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Tuple, Type


class ExecutorExceptionPolicies(Enum):
    """Runner exception policy modes."""

    restart = "restart"  # restart agent on fail, log exception
    stop_all = "stop_all"  # stop all agents on one agent's failure, log exception
    propagate = "propagate"  # log exception and reraise it to upper level
    log_only = "log_only"  # log exception and skip it


class AbstractExecutorTask(ABC):
    """Abstract task class to create Task classes."""

    def __init__(self):
        """Init task."""
        self._future: Optional[Awaitable] = None

    @property
    def future(self) -> Optional[Awaitable]:
        """Return awaitable to get result of task execution."""
        return self._future

    def set_future(self, future: Awaitable) -> None:
        """Set awaitable to get result of task execution."""
        self._future = future

    @abstractmethod
    def start(self):
        """Implement start task function here."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Implement stop task function here."""
        pass

    @abstractmethod
    def create_async_task(self, loop: AbstractEventLoop) -> Awaitable:
        """Return asyncio Task for task run in asyncio loop."""
        pass

    @property
    def id(self) -> Any:
        """Return task id."""
        return id(self)


class AbstractMultiprocessExecutorTask(AbstractExecutorTask):
    """Task for multiprocess executor."""

    @abstractmethod
    def start(self) -> Tuple[Callable, Sequence[Any]]:
        """Return function and arguments to call within subprocess."""
        pass

    def create_async_task(self, loop: AbstractEventLoop) -> Awaitable:
        """Raise error, cause async mode is not supported, cause this task for multiprocess executor only."""
        raise ValueError(
            "This task was designed only for multiprocess executor, not for async!"
        )


class AbstractMultipleExecutor(ABC):
    """Abstract class to create multiple executors classes."""

    def __init__(self, tasks: Sequence[AbstractExecutorTask]) -> None:
        """
        Init executor.

        :param tasks: sequence of AbstractExecutorTask instances to run.
        """
        self._tasks: Sequence[AbstractExecutorTask] = tasks
        self._is_running: bool = False
        self._future_task: Dict[Awaitable, AbstractExecutorTask] = {}
        self._loop: AbstractEventLoop = asyncio.new_event_loop()
        self._executor_pool: Optional[Executor] = None
        self._set_executor_pool()

    @property
    def is_running(self) -> bool:
        """Return running state of the executor."""
        return self._is_running

    def start(self) -> None:
        """Start tasks."""
        self._is_running = True
        self._start_tasks()
        self._loop.run_until_complete(self._wait_tasks_complete())

    def stop(self) -> None:
        """Stop tasks."""
        self._is_running = False
        for task in self._tasks:
            self._stop_task(task)
        if not self._loop.is_running():
            self._loop.run_until_complete(
                self._wait_tasks_complete(skip_exceptions=True)
            )

    def _start_tasks(self) -> None:
        """Schedule tasks."""
        for task in self._tasks:
            future = self._start_task(task)
            task.set_future(future)
            self._future_task[future] = task

    async def _wait_tasks_complete(self, skip_exceptions: bool = False) -> None:
        """
        Wait tasks execution to complete.

        :param skip_exceptions: skip exceptions if raised in tasks
        """
        done, pending = await asyncio.wait(
            self._future_task.keys(), return_when=FIRST_EXCEPTION
        )

        async def wait_task(task):
            try:
                await task
            except Exception:
                if not skip_exceptions:
                    raise

        for task in done:
            await wait_task(task)

        if pending:
            done, _ = await asyncio.wait(pending)
            for task in done:
                await wait_task(task)

    @abstractmethod
    def _start_task(self, task: AbstractExecutorTask) -> Awaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """

    @abstractmethod
    def _set_executor_pool(self) -> None:
        """Set executor pool to be used."""

    def _stop_task(self, task: AbstractExecutorTask) -> None:
        """
        Stop particular task.

        :param agent: AbstractExecutorTask instance to stop.
        :return: None
        """
        task.stop()


class ThreadExecutor(AbstractMultipleExecutor):
    """Thread based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Set thread pool pool to be used."""
        self._executor_pool = ThreadPoolExecutor(max_workers=len(self._tasks))

    def _start_task(self, task: AbstractExecutorTask) -> Awaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        return self._loop.run_in_executor(self._executor_pool, task.start)


class ProcessExecutor(ThreadExecutor):
    """Subprocess based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Set thread pool pool to be used."""
        self._executor_pool = ProcessPoolExecutor(max_workers=len(self._tasks))

    def _start_task(self, task: AbstractExecutorTask) -> Awaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        fn, args = task.start()
        return self._loop.run_in_executor(self._executor_pool, fn, *args)


class AsyncExecutor(AbstractMultipleExecutor):
    """Thread based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Do nothing, cause we run tasks in asyncio event loop and do not need an executor pool."""

    def _start_task(self, task: AbstractExecutorTask) -> Awaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        return task.create_async_task(self._loop)


class AbstractMultipleRunner:
    """Abstract multiple runner to create classes to launch tasks with selected mode."""

    SUPPORTED_MODES: Dict[str, Type[AbstractMultipleExecutor]] = {}

    def __init__(self, mode: str) -> None:
        """
        Init with selected executor mode.

        :param mode: one of supported executor modes
        """
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        self._mode: str = mode
        self._executor: AbstractMultipleExecutor = self._make_executor(mode)
        self._thread: Optional[Thread] = None

    @property
    def is_running(self) -> bool:
        """Return state of the executor."""
        return self._executor.is_running

    def start(self, threaded: bool = False) -> None:
        """
        Run agents.

        :param threaded: run in dedicated thread without blocking current thread.

        :return: None
        """
        self._is_running = True
        if threaded:
            self._thread = Thread(target=self._executor.start, daemon=True)
            self._thread.start()
        else:
            self._executor.start()

    def stop(self, timeout: float = 0) -> None:
        """
        Stop agents.

        :param timeout: timeout in seconds to wait thread stopped, only if started in thread mode.
        :return: None
        """
        self._is_running = False
        self._executor.stop()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _make_executor(self, mode: str) -> AbstractMultipleExecutor:
        """
        Make an executor instance to run agents with.

        :param agents: AEA instances to  run.
        :param mode: executor mode to use.

        :return: aea executor instance
        """
        executor_cls = self.SUPPORTED_MODES[mode]
        return executor_cls(tasks=self._make_tasks())

    @abstractmethod
    def _make_tasks(self) -> Sequence[AbstractExecutorTask]:
        """Make tasks to run with executor."""
        raise NotImplementedError

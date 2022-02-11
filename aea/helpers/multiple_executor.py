# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import logging
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from asyncio.tasks import FIRST_EXCEPTION, Task
from concurrent.futures._base import Executor, Future
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)


_default_logger = logging.getLogger(__name__)


TaskAwaitable = Union[Task, Future]


class ExecutorExceptionPolicies(Enum):
    """Runner exception policy modes."""

    stop_all = "stop_all"  # stop all agents on one agent's failure, log exception
    propagate = "propagate"  # log exception and reraise it to upper level
    log_only = "log_only"  # log exception and skip it


class AbstractExecutorTask(ABC):
    """Abstract task class to create Task classes."""

    def __init__(self) -> None:
        """Init task."""
        self._future: Optional[TaskAwaitable] = None

    @property
    def future(self) -> Optional[TaskAwaitable]:
        """Return awaitable to get result of task execution."""
        return self._future

    @future.setter
    def future(self, future: TaskAwaitable) -> None:
        """Set awaitable to get result of task execution."""
        self._future = future

    @abstractmethod
    def start(self) -> Tuple[Callable, Sequence[Any]]:
        """Implement start task function here."""

    @abstractmethod
    def stop(self) -> None:
        """Implement stop task function here."""

    @abstractmethod
    def create_async_task(self, loop: AbstractEventLoop) -> TaskAwaitable:
        """
        Create asyncio task for task run in asyncio loop.

        :param loop: the event loop
        :return: task to run in asyncio loop.
        """

    @property
    def id(self) -> Any:  # pragma: nocover
        """Return task id."""
        return id(self)

    @property
    def failed(self) -> bool:
        """
        Return was exception failed or not.

        If it's running it's not failed.

        :return: bool
        """
        if not self._future:
            return False

        if not self._future.done():
            return False

        if not self._future.exception():
            return False

        if isinstance(self._future.exception(), KeyboardInterrupt):
            return False

        return True


class AbstractMultiprocessExecutorTask(AbstractExecutorTask):
    """Task for multiprocess executor."""

    @abstractmethod
    def start(self) -> Tuple[Callable, Sequence[Any]]:
        """Return function and arguments to call within subprocess."""

    def create_async_task(
        self, loop: AbstractEventLoop
    ) -> TaskAwaitable:  # pragma: nocover
        """
        Create asyncio task for task run in asyncio loop.

        Raise error, cause async mode is not supported, cause this task for multiprocess executor only.

        :param loop: the event loop
        :raises ValueError: async task construction not possible
        """
        raise ValueError(
            "This task was designed only for multiprocess executor, not for async!"
        )


class AbstractMultipleExecutor(ABC):  # pragma: nocover
    """Abstract class to create multiple executors classes."""

    def __init__(
        self,
        tasks: Sequence[AbstractExecutorTask],
        task_fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate,
    ) -> None:
        """
        Init executor.

        :param tasks: sequence of AbstractExecutorTask instances to run.
        :param task_fail_policy: the exception policy of all the tasks
        """
        self._task_fail_policy: ExecutorExceptionPolicies = task_fail_policy
        self._tasks: Sequence[AbstractExecutorTask] = tasks
        self._is_running: bool = False
        self._future_task: Dict[TaskAwaitable, AbstractExecutorTask] = {}
        self._loop: AbstractEventLoop = asyncio.new_event_loop()
        self._executor_pool: Optional[Executor] = None
        self._set_executor_pool()

    @property
    def is_running(self) -> bool:
        """Return running state of the executor."""
        return self._is_running

    def start(self) -> None:
        """Start tasks."""
        self._start_tasks()
        self._loop.run_until_complete(self._wait_tasks_complete())
        self._is_running = False

    def stop(self) -> None:
        """Stop tasks."""
        self._is_running = False

        for task in self._tasks:
            self._stop_task(task)

        if not self._loop.is_running():
            self._loop.run_until_complete(
                self._wait_tasks_complete(skip_exceptions=True, on_stop=True)
            )

        if self._executor_pool:
            self._executor_pool.shutdown(wait=True)

    def _start_tasks(self) -> None:
        """Schedule tasks."""
        for task in self._tasks:
            future = self._start_task(task)
            task.future = future
            self._future_task[future] = task

    async def _wait_tasks_complete(
        self, skip_exceptions: bool = False, on_stop: bool = False
    ) -> None:
        """
        Wait tasks execution to complete.

        :param skip_exceptions: skip exceptions if raised in tasks
        :param on_stop: bool, indicating if stopping
        """
        if not on_stop:
            self._is_running = True

        pending = cast(Set[asyncio.futures.Future], set(self._future_task.keys()))

        async def wait_future(future: asyncio.futures.Future) -> None:
            try:
                await future
            except KeyboardInterrupt:  # pragma: nocover
                _default_logger.exception("KeyboardInterrupt in task!")
                if not skip_exceptions:
                    raise
            except Exception as e:  # pylint: disable=broad-except  # handle any exception with own code.
                _default_logger.exception("Exception in task!")
                if not skip_exceptions:
                    await self._handle_exception(
                        self._future_task[cast(TaskAwaitable, future)], e
                    )

        while pending:
            done, pending = await asyncio.wait(pending, return_when=FIRST_EXCEPTION)
            for future in done:
                await wait_future(future)

    async def _handle_exception(
        self, task: AbstractExecutorTask, exc: Exception
    ) -> None:
        """
        Handle exception raised during task execution.

        Log exception and process according to selected policy.

        :param task: task exception handled in
        :param exc: Exception raised
        """
        _default_logger.exception(f"Exception raised during {task.id} running.")
        _default_logger.info(f"Exception raised during {task.id} running.")
        if self._task_fail_policy == ExecutorExceptionPolicies.propagate:
            raise exc
        if self._task_fail_policy == ExecutorExceptionPolicies.log_only:
            pass
        elif self._task_fail_policy == ExecutorExceptionPolicies.stop_all:
            _default_logger.info(
                "Stopping executor according to fail policy cause exception raised in task"
            )
            self.stop()
            await self._wait_tasks_complete(skip_exceptions=True, on_stop=True)
        else:  # pragma: nocover
            raise ValueError(f"Unknown fail policy: {self._task_fail_policy}")

    @abstractmethod
    def _start_task(self, task: AbstractExecutorTask) -> TaskAwaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """

    @abstractmethod
    def _set_executor_pool(self) -> None:
        """Set executor pool to be used."""

    @staticmethod
    def _stop_task(task: AbstractExecutorTask) -> None:
        """
        Stop particular task.

        :param task: AbstractExecutorTask instance to stop.
        """
        task.stop()

    @property
    def num_failed(self) -> int:  # pragma: nocover
        """Return number of failed tasks."""
        return len(self.failed_tasks)

    @property
    def failed_tasks(self) -> Sequence[AbstractExecutorTask]:  # pragma: nocover
        """Return sequence failed tasks."""
        return [task for task in self._tasks if task.failed]

    @property
    def not_failed_tasks(self) -> Sequence[AbstractExecutorTask]:  # pragma: nocover
        """Return sequence successful tasks."""
        return [task for task in self._tasks if not task.failed]


class ThreadExecutor(AbstractMultipleExecutor):  # pragma: nocover
    """Thread based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Set thread pool pool to be used."""
        self._executor_pool = ThreadPoolExecutor(max_workers=len(self._tasks))

    def _start_task(self, task: AbstractExecutorTask) -> TaskAwaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        return cast(
            TaskAwaitable, self._loop.run_in_executor(self._executor_pool, task.start)
        )


class ProcessExecutor(ThreadExecutor):  # pragma: nocover
    """Subprocess based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Set thread pool pool to be used."""
        self._executor_pool = ProcessPoolExecutor(max_workers=len(self._tasks))

    def _start_task(self, task: AbstractExecutorTask) -> TaskAwaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        fn, args = task.start()
        return cast(
            TaskAwaitable, self._loop.run_in_executor(self._executor_pool, fn, *args)
        )


class AsyncExecutor(AbstractMultipleExecutor):  # pragma: nocover
    """Thread based executor to run multiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Do nothing, cause we run tasks in asyncio event loop and do not need an executor pool."""

    def _start_task(self, task: AbstractExecutorTask) -> TaskAwaitable:
        """
        Start particular task.

        :param task: AbstractExecutorTask instance to start.
        :return: awaitable object(future) to get result or exception
        """
        return task.create_async_task(self._loop)


class AbstractMultipleRunner:  # pragma: nocover
    """Abstract multiple runner to create classes to launch tasks with selected mode."""

    SUPPORTED_MODES: Dict[str, Type[AbstractMultipleExecutor]] = {}

    def __init__(
        self,
        mode: str,
        fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate,
    ) -> None:
        """
        Init with selected executor mode.

        :param mode: one of supported executor modes
        :param fail_policy: one of ExecutorExceptionPolicies to be used with Executor
        """
        if mode not in self.SUPPORTED_MODES:  # pragma: nocover
            raise ValueError(f"Unsupported mode: {mode}")
        self._mode: str = mode
        self._executor: AbstractMultipleExecutor = self._make_executor(
            mode, fail_policy
        )
        self._thread: Optional[Thread] = None

    @property
    def is_running(self) -> bool:
        """Return state of the executor."""
        return self._executor.is_running

    def start(self, threaded: bool = False) -> None:
        """
        Run agents.

        :param threaded: run in dedicated thread without blocking current thread.
        """
        if threaded:
            self._thread = Thread(target=self._executor.start, daemon=True)
            self._thread.start()
        else:
            self._executor.start()

    def stop(self, timeout: Optional[float] = None) -> None:
        """
        Stop agents.

        :param timeout: timeout in seconds to wait thread stopped, only if started in thread mode.
        """
        self._executor.stop()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _make_executor(
        self, mode: str, fail_policy: ExecutorExceptionPolicies
    ) -> AbstractMultipleExecutor:
        """
        Make an executor instance to run agents with.

        :param mode: executor mode to use.
        :param fail_policy: one of ExecutorExceptionPolicies to be used with Executor

        :return: aea executor instance
        """
        executor_cls = self.SUPPORTED_MODES[mode]
        return executor_cls(tasks=self._make_tasks(), task_fail_policy=fail_policy)

    @abstractmethod
    def _make_tasks(self) -> Sequence[AbstractExecutorTask]:
        """Make tasks to run with executor."""

    @property
    def num_failed(self) -> int:  # pragma: nocover
        """Return number of failed tasks."""
        return self._executor.num_failed

    @property
    def failed(self) -> Sequence[Task]:  # pragma: nocover
        """Return sequence failed tasks."""
        return [i.id for i in self._executor.failed_tasks]

    @property
    def not_failed(self) -> Sequence[Task]:  # pragma: nocover
        """Return sequence successful tasks."""
        return [i.id for i in self._executor.not_failed_tasks]

    def try_join_thread(self) -> None:  # pragma: nocover
        """Try to join thread if running in thread mode."""
        if self._thread is None:
            raise ValueError("Not started in thread mode.")
        # do not block with join, helpful to catch KeyboardInterrupt exception
        while self._thread.is_alive():
            self._thread.join(0.1)

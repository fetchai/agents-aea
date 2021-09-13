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
"""This module contains the classes for tasks."""
import logging
import signal
import threading
from abc import abstractmethod
from multiprocessing.pool import AsyncResult, Pool, ThreadPool
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, cast

from aea.components.utils import _enlist_component_packages, _populate_packages
from aea.helpers.logging import WithLogger


THREAD_POOL_MODE = "multithread"
PROCESS_POOL_MODE = "multiprocess"
DEFAULT_WORKERS_AMOUNT = 2


class Task(WithLogger):
    """This class implements an abstract task."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a task."""
        super().__init__(**kwargs)
        self._is_executed = False
        # this is where we store the result.
        self._result = None
        self.config = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the task.

        :param args: positional arguments forwarded to the 'execute' method.
        :param kwargs: keyword arguments forwarded to the 'execute' method.
        :return: the task instance
        :raises ValueError: if the task has already been executed.
        """
        if self._is_executed:
            raise ValueError("Task already executed.")

        self.setup()
        try:
            self._result = self.execute(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.debug(
                "Got exception of type {} with message '{}' while executing task.".format(
                    type(e), str(e)
                )
            )
        finally:
            self._is_executed = True
            self.teardown()
        return self._result

    @property
    def is_executed(self) -> bool:
        """Check if the task has already been executed."""
        return self._is_executed

    @property
    def result(self) -> Any:
        """
        Get the result.

        :return: the result from the execute method.
        :raises ValueError: if the task has not been executed yet.
        """
        if not self._is_executed:
            raise ValueError("Task not executed yet.")
        return self._result

    def setup(self) -> None:
        """Implement the task setup."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run the task logic.

        :param args: the positional arguments
        :param kwargs: the keyword arguments
        :return: any
        """

    def teardown(self) -> None:
        """Implement the task teardown."""


# for api compatability. to remove in the next release
def init_worker() -> None:  # pragma: nocover
    """
    Initialize a worker.

    Disable the SIGINT handler of process pool is using.
    Related to a well-known bug: https://bugs.python.org/issue8296
    """
    if Pool.__class__.__name__ == "Pool":  # pragma: nocover
        # Process worker
        signal.signal(signal.SIGINT, signal.SIG_IGN)


def _init_worker(mode: str, packages: Dict[str, List[Dict[str, str]]]) -> None:
    """
    Initialize a worker.

    Disable the SIGINT handler of process pool is using.
    Related to a well-known bug: https://bugs.python.org/issue8296

    :param mode: str. mode task manager runs in
    :param packages: dict with list of packages to load if needed
    """
    if mode == PROCESS_POOL_MODE:  # pragma: nocover
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        _populate_packages(packages)


class TaskManager(WithLogger):
    """A Task manager."""

    POOL_MODES: Dict[str, Type[Pool]] = {
        THREAD_POOL_MODE: ThreadPool,
        PROCESS_POOL_MODE: Pool,
    }

    def __init__(
        self,
        nb_workers: int = DEFAULT_WORKERS_AMOUNT,
        is_lazy_pool_start: bool = True,
        logger: Optional[logging.Logger] = None,
        pool_mode: str = THREAD_POOL_MODE,
    ) -> None:
        """
        Initialize the task manager.

        :param nb_workers: the number of worker processes.
        :param is_lazy_pool_start: option to postpone pool creation till the first enqueue_task called.
        :param logger: the logger.
        :param pool_mode: str. multithread or multiprocess
        """
        WithLogger.__init__(self, logger)
        self._nb_workers = nb_workers
        self._is_lazy_pool_start = is_lazy_pool_start
        self._pool = None  # type: Optional[Pool]
        self._stopped = True
        self._lock = threading.Lock()

        self._task_enqueued_counter = 0
        self._results_by_task_id = {}  # type: Dict[int, Any]
        self._pool_mode = pool_mode

    @property
    def is_started(self) -> bool:
        """
        Get started status of TaskManager.

        :return: bool
        """
        return not self._stopped

    @property
    def nb_workers(self) -> int:
        """
        Get the number of workers.

        :return: int
        """
        return self._nb_workers

    def enqueue_task(
        self,
        func: Callable,
        args: Sequence = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Enqueue a task with the executor.

        :param func: the callable instance to be enqueued
        :param args: the positional arguments to be passed to the function.
        :param kwargs: the keyword arguments to be passed to the function.
        :return: the task id to get the the result.
        :raises ValueError: if the task manager is not running.
        """
        with self._lock:
            if self._stopped:
                raise ValueError("Task manager not running.")

            if not self._pool and self._is_lazy_pool_start:
                self._start_pool()

            self._pool = cast(Pool, self._pool)
            task_id = self._task_enqueued_counter
            self._task_enqueued_counter += 1
            async_result = self._pool.apply_async(
                func, args=args, kwds=kwargs if kwargs is not None else {}
            )

            self._results_by_task_id[task_id] = async_result
            if self._logger:  # pragma: nocover
                self._logger.info(f"Task <{func}{args}> set. Task id is {task_id}")
            return task_id

    def get_task_result(self, task_id: int) -> AsyncResult:
        """
        Get the result from a task.

        :param task_id: the task id
        :return: async result for task_id
        """
        task_result = self._results_by_task_id.get(
            task_id, None
        )  # type: Optional[AsyncResult]
        if task_result is None:
            raise ValueError("Task id {} not present.".format(task_id))

        return task_result

    def start(self) -> None:
        """Start the task manager."""
        with self._lock:
            if self._stopped is False:
                self.logger.debug("Task manager already running.")
            else:
                self.logger.debug("Start the task manager.")
                self._stopped = False
                if not self._is_lazy_pool_start:
                    self._start_pool()

    def stop(self) -> None:
        """Stop the task manager."""
        with self._lock:
            if self._stopped is True:
                self.logger.debug("Task manager already stopped.")
            else:
                self.logger.debug("Stop the task manager.")
                self._stopped = True
                self._stop_pool()

    def _start_pool(self) -> None:
        """
        Start internal task pool.

        Only one pool will be created.
        """
        if self._pool:
            self.logger.debug("Pool was already started!")
            return
        pool_cls = self.POOL_MODES.get(self._pool_mode)
        if not pool_cls:  # pragma: nocover
            raise ValueError(f"Mode: `{self._pool_mode}` is not supported")
        init_args = (
            self._pool_mode,
            _enlist_component_packages(),
        )
        self._pool = pool_cls(
            self._nb_workers, initializer=_init_worker, initargs=init_args
        )

    def _stop_pool(self) -> None:
        """Stop internal task pool."""
        if not self._pool:
            self.logger.debug("Pool is not started!.")
            return

        self._pool = cast(Pool, self._pool)
        self._pool.terminate()
        self._pool.join()
        self._pool = None


class ThreadedTaskManager(TaskManager):
    """A threaded task manager."""

    def __init__(
        self,
        nb_workers: int = DEFAULT_WORKERS_AMOUNT,
        is_lazy_pool_start: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize the task manager.

        :param nb_workers: the number of worker processes.
        :param is_lazy_pool_start: option to postpone pool creation till the first enqueue_task called.
        :param logger: the logger.
        """
        super().__init__(
            nb_workers=nb_workers,
            is_lazy_pool_start=is_lazy_pool_start,
            logger=logger,
            pool_mode=THREAD_POOL_MODE,
        )


class ProcessTaskManager(TaskManager):
    """A multiprocess task manager."""

    def __init__(
        self,
        nb_workers: int = DEFAULT_WORKERS_AMOUNT,
        is_lazy_pool_start: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize the task manager.

        :param nb_workers: the number of worker processes.
        :param is_lazy_pool_start: option to postpone pool creation till the first enqueue_task called.
        :param logger: the logger.
        """
        super().__init__(
            nb_workers=nb_workers,
            is_lazy_pool_start=is_lazy_pool_start,
            logger=logger,
            pool_mode=PROCESS_POOL_MODE,
        )

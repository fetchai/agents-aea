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
"""This module contains the implementation of multiple AEA configs launcher."""
import multiprocessing
from asyncio.events import AbstractEventLoop
from multiprocessing.synchronize import Event
from os import PathLike
from threading import Thread
from typing import Any, Awaitable, Callable, Dict, Sequence, Tuple, Type, Union

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.exceptions import AEAException
from aea.helpers.base import cd
from aea.helpers.multiple_executor import (
    AbstractExecutorTask,
    AbstractMultipleExecutor,
    AbstractMultipleRunner,
    AbstractMultiprocessExecutorTask,
    AsyncExecutor,
    ExecutorExceptionPolicies,
    ProcessExecutor,
    ThreadExecutor,
)
from aea.runtime import AsyncRuntime


def load_agent(agent_dir: Union[PathLike, str]) -> AEA:
    """
    Load AEA from directory.

    :param agent_dir: agent configuration directory

    :return: AEA instance
    """
    with cd(agent_dir):
        return AEABuilder.from_aea_project(".").build()


def _run_agent(agent_dir: Union[PathLike, str], stop_event: Event) -> None:
    """
    Load and run agent in a dedicated process.

    :param agent_dir: agent configuration directory
    :param stop_event: multithreading Event to stop agent run.

    :return: None
    """
    agent = load_agent(agent_dir)

    def stop_event_thread():
        stop_event.wait()
        agent.stop()

    Thread(target=stop_event_thread, daemon=True).start()
    try:
        agent.start()
    except Exception as e:
        exc = AEAException(f"Raised {type(e)}({e})")
        exc.__traceback__ = e.__traceback__
        raise exc
    finally:
        stop_event.set()


class AEADirTask(AbstractExecutorTask):
    """Task to run agent from agent configuration directory."""

    def __init__(self, agent_dir: Union[PathLike, str]) -> None:
        """
        Init aea config dir task.

        :param agent_dir: direcory with aea config.
        """
        self._agent_dir = agent_dir
        self._agent: AEA = load_agent(self._agent_dir)
        super().__init__()

    def start(self) -> None:
        """Start task."""
        self._agent.start()

    def stop(self):
        """Stop task."""
        if not self._agent:
            raise Exception("Task was not started!")
        self._agent.stop()

    def create_async_task(self, loop: AbstractEventLoop) -> Awaitable:
        """Return asyncio Task for task run in asyncio loop."""
        self._agent.runtime.set_loop(loop)
        if not isinstance(self._agent.runtime, AsyncRuntime):
            raise ValueError(
                "Agent runtime is not async compatible. Please use runtime_mode=async"
            )
        return loop.create_task(self._agent.runtime.run_runtime())

    @property
    def id(self) -> Union[PathLike, str]:
        """Return agent_dir."""
        return self._agent_dir


class AEADirMultiprocessTask(AbstractMultiprocessExecutorTask):
    """
    Task to run agent from agent configuration directory.

    Version for multiprocess executor mode.
    """

    def __init__(self, agent_dir: Union[PathLike, str]):
        """
        Init aea config dir task.

        :param agent_dir: direcory with aea config.
        """
        self._agent_dir = agent_dir
        self._manager = multiprocessing.Manager()
        self._stop_event = self._manager.Event()
        super().__init__()

    def start(self) -> Tuple[Callable, Sequence[Any]]:
        """Return function and arguments to call within subprocess."""
        return (_run_agent, (self._agent_dir, self._stop_event))

    def stop(self):
        """Stop task."""
        self._stop_event.set()

    @property
    def id(self) -> Union[PathLike, str]:
        """Return agent_dir."""
        return self._agent_dir


class AEALauncher(AbstractMultipleRunner):
    """Run multiple AEA instances."""

    SUPPORTED_MODES: Dict[str, Type[AbstractMultipleExecutor]] = {
        "threaded": ThreadExecutor,
        "async": AsyncExecutor,
        "multiprocess": ProcessExecutor,
    }

    def __init__(
        self,
        agent_dirs: Sequence[Union[PathLike, str]],
        mode: str,
        fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate,
    ) -> None:
        """
        Init AEARunner.

        :param agent_dirs: sequence of AEA config directories.
        :param mode: executor name to use.
        :param fail_policy: one of ExecutorExceptionPolicies to be used with Executor
        """
        self._agent_dirs = agent_dirs
        super().__init__(mode=mode, fail_policy=fail_policy)

    def _make_tasks(self) -> Sequence[AbstractExecutorTask]:
        """Make tasks to run with executor."""
        if self._mode == "multiprocess":
            return [AEADirMultiprocessTask(agent_dir) for agent_dir in self._agent_dirs]
        else:
            return [AEADirTask(agent_dir) for agent_dir in self._agent_dirs]

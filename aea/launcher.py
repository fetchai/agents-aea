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
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing.synchronize import Event
from os import PathLike
from threading import Thread
from typing import Awaitable, Dict, List, Optional, Sequence, Type

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.exceptions import AEAException
from aea.helpers.base import cd
from aea.runner import AsyncExecutor, BaseAEAExecutor, ThreadExecutor


def load_agent(agent_dir: PathLike) -> AEA:
    """
    Load AEA from directory.

    :param agent_dir: agent configuration directory

    :return: AEA instance
    """
    with cd(agent_dir):
        return AEABuilder.from_aea_project(".").build()


def _run_agent(agent_dir: PathLike, stop_event: Event) -> None:
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


class ProcessExecutor(BaseAEAExecutor):
    """
    AEA executor uses subprocess to run multiple AEAs.

    Support only AEA direcories, not instances.
    """

    def __init__(self, agent_dirs: Sequence[PathLike]) -> None:
        """
        Init executor.

        :param agents: sequence of agents dirs to run.
        """
        super().__init__(agent_dirs)  # type: ignore # tricky part, cause need to pass str instead of AEA
        self._agents: Sequence[PathLike] = agent_dirs  # type: ignore # tricky part, cause need to pass str instead of AEA
        self._task_stop_event: Dict[Awaitable, Event] = {}

    def _set_executor_pool(self):
        """Set ProcessPoolExecutor to be used."""
        self._executor_pool = ProcessPoolExecutor(max_workers=len(self._agents))
        self._manager = multiprocessing.Manager()

    def _start_agent(self, agent_dir: PathLike) -> Awaitable:  # type: ignore # tricky part, cause need to pass str instead of AEA
        """
        Start particular agent.

        :param agent: agent dir with configuration to start.
        :return: awaitable task to get result or exception
        """
        stop_event = self._manager.Event()
        task = self._loop.run_in_executor(
            self._executor_pool, _run_agent, agent_dir, stop_event
        )
        self._task_stop_event[task] = stop_event
        return task

    def _stop_agent(self, agent_dir: PathLike):  # type: ignore # tricky part, cause need to pass str instead of AEA
        """
        Stop particular agent.

        :param agent: AEA instance to stop.
        :return: None
        """
        task = self._agent_task[agent_dir]  # type: ignore # tricky part, cause need to pass str instead of AEA
        stop_event = self._task_stop_event[task]
        stop_event.set()


class BaseLaunchExecutor:
    """Base launch executor to implement executors."""

    RUNNER_EXECUTOR_CLASS: Optional[Type[BaseAEAExecutor]] = None

    def __init__(self, agent_dirs: List[PathLike]) -> None:
        """
        Inin launche executor.

        :param agent_dirs: sequence of agents configuration directories.
        """
        self._agent_dirs = agent_dirs
        self._runner: Optional[BaseAEAExecutor] = None
        if not self.RUNNER_EXECUTOR_CLASS:
            raise ValueError("RUNNER_EXECUTOR_CLASS has to be specified!")

    def _make_agents(self) -> Sequence[AEA]:
        """
        Load agents from directories.

        :return: sequence of AEA instances.
        """
        return [load_agent(agent_dir) for agent_dir in self._agent_dirs]

    def start(self) -> None:
        """Start agents."""
        agents = self._make_agents()
        self._runner = self.RUNNER_EXECUTOR_CLASS(agents)  # type: ignore # pylint: disable=E1102    # checked on init
        self._runner.start()

    def stop(self) -> None:
        """Stop agents."""
        if not self._runner:
            raise Exception("not started")
        self._runner.stop()

    @property
    def is_running(self) -> bool:
        """
        Return running state of the launcher executor.

        :return: bool
        """
        return bool(self._runner) and self._runner.is_running  # type: ignore  # checked on init


class _AsyncLauncherExecutor(BaseLaunchExecutor):
    """Launcher uses shared asyncio event loop to run multiple agents."""

    RUNNER_EXECUTOR_CLASS = AsyncExecutor


class _ThreadLauncherExecutor(BaseLaunchExecutor):
    """Launcher uses multiple threads to run multiple agents."""

    RUNNER_EXECUTOR_CLASS = ThreadExecutor


class _ProcessLauncherExecutor(BaseLaunchExecutor):
    """Launcher uses subprocesses to run multiple agents."""

    RUNNER_EXECUTOR_CLASS = ProcessExecutor

    def _make_agents(self) -> Sequence[PathLike]:  # type: ignore  # cause need strs for subprocesses
        """Return sequence of agents dirs."""
        return list(self._agent_dirs)


class AEALauncher:
    """Launch multiple AEA from dirs."""

    SUPPORTED_MODES: Dict[str, Type[BaseLaunchExecutor]] = {
        "thread": _ThreadLauncherExecutor,
        "async": _AsyncLauncherExecutor,
        "process": _ProcessLauncherExecutor,
    }

    def __init__(self, agent_dirs: List[PathLike], mode: str) -> None:
        """
        Init AEARunner.

        :param agents: sequence of AEA instances to run.
        """
        self.agent_dirs: List[PathLike] = agent_dirs
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        self._mode = mode
        self._executor = self._make_executor(agent_dirs, mode)
        self._thread = None

    def _make_executor(
        self, agent_dirs: List[PathLike], mode: str
    ) -> BaseLaunchExecutor:
        """
        Construct executor.

        :param: agent_dirs: sequence of agents dirs to start.
        :param mode: executor mode

        :return: launch executor to use.
        """
        executor_cls = self.SUPPORTED_MODES[mode]
        return executor_cls(agent_dirs=agent_dirs)

    @property
    def is_running(self):
        """
        Return running state of the launcher executor.

        :return: bool
        """
        return self._executor.is_running

    def start(self, threaded=False):
        """
        Run agents.

        :param threaded: run in dedicated thread without blockg current thread.

        :return: None
        """
        self._is_running = True
        if threaded:
            self._thread = Thread(target=self._executor.start, daemon=True)
            self._thread.start()
        else:
            self._executor.start()

    def stop(self):
        """Stop agents."""
        self._is_running = False
        self._executor.stop()

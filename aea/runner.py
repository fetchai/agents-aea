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
"""This module contains the implementation of AEA multiple instances runner."""
import asyncio
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from asyncio.tasks import FIRST_EXCEPTION
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Thread
from typing import Awaitable, Dict, Optional, Sequence, Type

from aea.aea import AEA


class BaseAEAExecutor(ABC):
    """Base AEA executor to impmlement aea executors to run multiple agents."""

    def __init__(self, agents: Sequence[AEA]) -> None:
        """
        Init executor.

        :param agents: sequence of AEA instances to run.
        """
        self._agents: Sequence[AEA] = agents
        self._is_running: bool = False
        self._agent_task: Dict[AEA, Awaitable] = {}
        self._task_agent: Dict[Awaitable, AEA] = {}
        self._loop: AbstractEventLoop = asyncio.new_event_loop()
        self._set_executor_pool()

    @property
    def is_running(self) -> bool:
        """Return running state of the executor."""
        return self._is_running

    def start(self) -> None:
        """Start agents."""
        self._is_running = True
        self._start_agents()
        self._loop.run_until_complete(self._wait_tasks())

    def stop(self) -> None:
        """Stop agents."""
        self._is_running = False
        for agent in self._agents:
            self._stop_agent(agent)
        if not self._loop.is_running():
            self._loop.run_until_complete(self._wait_tasks(skip_exceptions=True))

    def _start_agents(self) -> None:
        """Start agents tasks."""
        for agent in self._agents:
            task = self._start_agent(agent)
            self._agent_task[agent] = task
            self._task_agent[task] = agent

    async def _wait_tasks(self, skip_exceptions: bool = False) -> None:
        """
        Wait agents tasks to complete.

        :param skip_exceptions: skip exceptions if raised in tasks
        """
        done, pending = await asyncio.wait(
            self._task_agent.keys(), return_when=FIRST_EXCEPTION
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
    def _start_agent(self, agent: AEA) -> Awaitable:
        """
        Start particular agent.

        :param agent: AEA instance to start.
        :return: awaitable task to get result or exception
        """

    @abstractmethod
    def _stop_agent(self, agent: AEA) -> None:
        """
        Stop particular agent.

        :param agent: AEA instance to stop.
        :return: None
        """

    @abstractmethod
    def _set_executor_pool(self) -> None:
        """Set executor pool to be used."""


class ThreadExecutor(BaseAEAExecutor):
    """Thread based executor to run mul,tiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Set thread pool pool to be used."""
        self._executor_pool = ThreadPoolExecutor(max_workers=len(self._agents))

    def _start_agent(self, agent: AEA) -> Awaitable:
        """
        Start particular agent.

        :param agent: AEA instance to start.
        :return: awaitable task to get result or exception
        """
        return self._loop.run_in_executor(self._executor_pool, agent.start)

    def _stop_agent(self, agent: AEA) -> None:
        """
        Stop particular agent.

        :param agent: AEA instance to stop.
        :return: None
        """
        agent.stop()


class AsyncExecutor(BaseAEAExecutor):
    """Thread based executor to run mul,tiple agents in threads."""

    def _set_executor_pool(self) -> None:
        """Do nothing, cause we run tasks in asyncio event loop and do not need an executor pool."""

    def _start_agent(self, agent: AEA) -> Awaitable:
        """
        Start particular agent.

        :param agent: AEA instance to start.
        :return: awaitable task to get result or exception
        """
        if agent._runtime_mode != "async":
            raise ValueError(
                "Agent has to use async runtime mode to run with Async mode runner."
            )
        agent._runtime.set_loop(self._loop)
        return self._loop.create_task(agent._runtime._run_runtime())  # type: ignore # checked above

    def _stop_agent(self, agent: AEA) -> None:
        """
        Stop particular agent.

        :param agent: AEA instance to stop.
        :return: None
        """
        agent.stop()


class AEARunner:
    """Run multiple AEA instances."""

    SUPPORTED_MODES: Dict[str, Type[BaseAEAExecutor]] = {
        "threaded": ThreadExecutor,
        "async": AsyncExecutor,
    }

    def __init__(self, agents: Sequence[AEA], mode: str) -> None:
        """
        Init AEARunner.

        :param agents: sequence of AEA instances to run.
        :param mode: executor name to use.
        """
        self.agents: Sequence[AEA] = agents
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        self._mode: str = mode
        self._executor: BaseAEAExecutor = self._make_executor(agents, mode)
        self._thread: Optional[Thread] = None

    def _make_executor(self, agents: Sequence[AEA], mode: str) -> BaseAEAExecutor:
        """
        Make an executor instance to run agents with.

        :param agents: AEA instances to  run.
        :param mode: executor mode to use.

        :return: aea executor instance
        """
        executor_cls = self.SUPPORTED_MODES[mode]
        return executor_cls(agents=agents)

    @property
    def is_running(self) -> bool:
        """Return state of the executor."""
        return self._executor.is_running

    def start(self, threaded: bool = False) -> None:
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

    def stop(self) -> None:
        """Stop agents."""
        self._is_running = False
        self._executor.stop()

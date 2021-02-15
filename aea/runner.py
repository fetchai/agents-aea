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
import logging
from asyncio.events import AbstractEventLoop
from typing import Dict, Sequence, Type

from aea.aea import AEA
from aea.helpers.multiple_executor import (
    AbstractExecutorTask,
    AbstractMultipleExecutor,
    AbstractMultipleRunner,
    AsyncExecutor,
    ExecutorExceptionPolicies,
    TaskAwaitable,
    ThreadExecutor,
)
from aea.runtime import AsyncRuntime


_default_logger = logging.getLogger(__name__)


class AEAInstanceTask(AbstractExecutorTask):
    """Task to run agent instance."""

    def __init__(self, agent: AEA) -> None:
        """
        Init aea instance task.

        :param agent: AEA instance to run within task.
        """
        self._agent = agent
        super().__init__()

    @property
    def id(self) -> str:
        """Return agent name."""
        return self._agent.name

    def start(self) -> None:  # type: ignore
        """Start task."""
        try:
            self._agent.start()
        except BaseException:
            _default_logger.exception("Exceptions raised in runner task.")
            raise

    def stop(self) -> None:
        """Stop task."""
        self._agent.runtime.stop()

    def create_async_task(self, loop: AbstractEventLoop) -> TaskAwaitable:
        """
        Return asyncio Task for task run in asyncio loop.

        :param loop: abstract event loop
        :return: task to run runtime
        """
        self._agent.runtime.set_loop(loop)
        if not isinstance(self._agent.runtime, AsyncRuntime):  # pragma: nocover
            raise ValueError(
                "Agent runtime is not async compatible. Please use runtime_mode=async"
            )
        return loop.create_task(self._agent.runtime.start_and_wait_completed())


class AEARunner(AbstractMultipleRunner):
    """Run multiple AEA instances."""

    SUPPORTED_MODES: Dict[str, Type[AbstractMultipleExecutor]] = {
        "threaded": ThreadExecutor,
        "async": AsyncExecutor,
    }

    def __init__(
        self,
        agents: Sequence[AEA],
        mode: str,
        fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate,
    ) -> None:
        """
        Init AEARunner.

        :param agents: sequence of AEA instances to run.
        :param mode: executor name to use.
        :param fail_policy: one of ExecutorExceptionPolicies to be used with Executor
        """
        self._agents = agents
        super().__init__(mode=mode, fail_policy=fail_policy)

    def _make_tasks(self) -> Sequence[AbstractExecutorTask]:
        """Make tasks to run with executor."""
        return [AEAInstanceTask(agent) for agent in self._agents]

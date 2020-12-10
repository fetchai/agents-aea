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
"""This module contains the implementation of runtime for economic agent (AEA)."""
import asyncio
from asyncio.events import AbstractEventLoop
from concurrent.futures._base import CancelledError
from contextlib import suppress
from enum import Enum
from typing import Dict, Optional, Type, cast

from aea.abstract_agent import AbstractAgent
from aea.agent_loop import AsyncAgentLoop, AsyncState, BaseAgentLoop, SyncAgentLoop
from aea.connections.base import ConnectionStates
from aea.decision_maker.base import DecisionMaker, DecisionMakerHandler
from aea.exceptions import _StopRuntime
from aea.helpers.async_utils import Runnable
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.logging import WithLogger, get_logger
from aea.helpers.storage.generic_storage import Storage
from aea.multiplexer import AsyncMultiplexer
from aea.skills.tasks import TaskManager


class RuntimeStates(Enum):
    """Runtime states."""

    starting = "starting"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    error = "error"


class BaseRuntime(Runnable, WithLogger):
    """Abstract runtime class to create implementations."""

    RUN_LOOPS: Dict[str, Type[BaseAgentLoop]] = {
        "async": AsyncAgentLoop,
        "sync": SyncAgentLoop,
    }
    DEFAULT_RUN_LOOP: str = "async"

    def __init__(
        self,
        agent: AbstractAgent,
        loop_mode: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        threaded: bool = False,
    ) -> None:
        """
        Init runtime.

        :param agent: Agent to run.
        :param loop_mode: agent main loop mode.
        :param loop: optional event loop. if not provided a new one will be created.
        :return: None
        """
        Runnable.__init__(self, threaded=threaded, loop=loop if not threaded else None)
        logger = get_logger(__name__, agent.name)
        WithLogger.__init__(self, logger=logger)
        self._agent: AbstractAgent = agent
        self._state: AsyncState = AsyncState(RuntimeStates.stopped, RuntimeStates)
        self._state.add_callback(self._log_runtime_state)

        self._multiplexer: AsyncMultiplexer = self._get_multiplexer_instance()
        self._task_manager = TaskManager()
        self._decision_maker: Optional[DecisionMaker] = None
        self._storage: Optional[Storage] = self._get_storage(agent)

        self._loop_mode = loop_mode or self.DEFAULT_RUN_LOOP
        self.main_loop: BaseAgentLoop = self._get_main_loop_instance(self._loop_mode)

    @staticmethod
    def _get_storage(agent) -> Optional[Storage]:
        """Get storage instance if storage_uri provided."""
        if agent.storage_uri:
            # threaded has to be always True, cause syncrhonous operations are supported
            return Storage(agent.storage_uri, threaded=True)
        return None  # pragma: nocover

    @property
    def storage(self) -> Optional[Storage]:
        """Get optional storage."""
        return self._storage

    @property
    def loop_mode(self) -> str:  # pragma: nocover
        """Get current loop mode."""
        return self._loop_mode

    def setup_multiplexer(self) -> None:
        """Set up the multiplexer."""
        setup_options = self._agent.get_multiplexer_setup_options()
        if setup_options:
            self.multiplexer.setup(**setup_options)

    @property
    def task_manager(self) -> TaskManager:
        """Get the task manager."""
        return self._task_manager

    @property
    def loop(self) -> Optional[AbstractEventLoop]:
        """Get event loop."""
        return self._loop

    @property
    def multiplexer(self) -> AsyncMultiplexer:
        """Get multiplexer."""
        return self._multiplexer

    def _get_multiplexer_instance(self) -> AsyncMultiplexer:
        """Create multiplexer instance."""
        exception_policy = getattr(
            self._agent, "_connection_exception_policy", ExceptionPolicyEnum.propagate
        )
        return AsyncMultiplexer(
            self._agent.connections,
            loop=self.loop,
            exception_policy=exception_policy,
            agent_name=self._agent.name,
        )

    def _get_main_loop_class(self, loop_mode: str) -> Type[BaseAgentLoop]:
        """
        Get main loop class based on loop mode.

        :param: loop_mode: str.

        :return: MainLoop class
        """
        if loop_mode not in self.RUN_LOOPS:  # pragma: nocover
            raise ValueError(
                f"Loop `{loop_mode} is not supported. valid are: `{list(self.RUN_LOOPS.keys())}`"
            )
        return self.RUN_LOOPS[loop_mode]

    def _set_task(self):
        self._task = self._loop.create_task(self._run_wrapper())

    @property
    def decision_maker(self) -> DecisionMaker:
        """Return decision maker if set."""
        if self._decision_maker is None:  # pragma: nocover
            raise ValueError("call `set_decision_maker` first!")
        return self._decision_maker

    def set_decision_maker(self, decision_maker_handler: DecisionMakerHandler) -> None:
        """Set decision maker with handler provided."""
        self._decision_maker = DecisionMaker(
            decision_maker_handler=decision_maker_handler
        )

    def _get_main_loop_instance(self, loop_mode: str) -> BaseAgentLoop:
        """
        Construct main loop instance.

        :param: loop_mode: str.

        :return: AgentLoop instance
        """
        loop_cls = self._get_main_loop_class(loop_mode)
        return loop_cls(self._agent)

    def _log_runtime_state(self, state) -> None:
        """Log a runtime state changed."""
        self.logger.debug(f"[{self._agent.name}]: Runtime state changed to {state}.")

    def _teardown(self) -> None:
        """Tear down runtime."""
        self.logger.debug("[{}]: Runtime teardown...".format(self._agent.name))
        if self._decision_maker is not None:  # pragma: nocover
            self.decision_maker.stop()
        self.task_manager.stop()
        self.logger.debug("[{}]: Calling teardown method...".format(self._agent.name))
        self._agent.teardown()
        self.logger.debug("[{}]: Runtime teardown completed".format(self._agent.name))

    @property
    def is_running(self) -> bool:
        """Get running state of the runtime."""
        return self._state.get() == RuntimeStates.running

    @property
    def is_stopped(self) -> bool:  # pragma: nocover
        """Get stopped state of the runtime."""
        return self._state.get() in [RuntimeStates.stopped]

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop to be used.

        :param loop: event loop to use.
        """
        self._loop = loop
        asyncio.set_event_loop(self._loop)

    @property
    def state(self) -> RuntimeStates:  # pragma: nocover
        """
        Get runtime state.

        :return: RuntimeStates
        """
        return cast(RuntimeStates, self._state.get())


class AsyncRuntime(BaseRuntime):
    """Asynchronous runtime: uses asyncio loop for multiplexer and async agent main loop."""

    def __init__(
        self,
        agent: AbstractAgent,
        loop_mode: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        threaded=False,
    ) -> None:
        """
        Init runtime.

        :param agent: Agent to run.
        :param loop_mode: agent main loop mode.
        :param loop: optional event loop. if not provided a new one will be created.
        :return: None
        """
        super().__init__(agent=agent, loop_mode=loop_mode, loop=loop, threaded=threaded)
        self._task: Optional[asyncio.Task] = None

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop to be used.

        :param loop: event loop to use.
        """
        BaseRuntime.set_loop(self, loop)

    async def run(self) -> None:
        """
        Start runtime task.

        Starts multiplexer and agent loop.
        """
        terminal_state = RuntimeStates.error
        try:
            await self.run_runtime()
        except _StopRuntime as e:
            self._state.set(RuntimeStates.stopping)
            terminal_state = RuntimeStates.stopped
            if e.reraise:
                raise e.reraise
        except (asyncio.CancelledError, CancelledError, KeyboardInterrupt):
            self._state.set(RuntimeStates.stopping)
            terminal_state = RuntimeStates.stopped
        finally:
            await self.stop_runtime()
            self._state.set(terminal_state)

    async def stop_runtime(self) -> None:
        """
        Stop runtime coroutine.

        Stop main loop.
        Tear down the agent..
        Disconnect multiplexer.
        """
        self.main_loop.stop()
        with suppress(_StopRuntime):
            await self.main_loop.wait_completed()
        self._teardown()

        if self._storage is not None:
            self._storage.stop()
            await self._storage.wait_completed()

        self.multiplexer.stop()
        await self.multiplexer.wait_completed()
        self.logger.debug("Runtime loop stopped!")

    async def run_runtime(self) -> None:
        """Run agent and starts multiplexer."""
        self._state.set(RuntimeStates.starting)
        await asyncio.gather(
            self._start_multiplexer(), self._start_agent_loop(), self._start_storage()
        )

    async def _start_storage(self) -> None:
        """Start storage component."""
        if self._storage is not None:
            self._storage.start()
            await self._storage.wait_completed()

    async def _start_multiplexer(self) -> None:
        """Call multiplexer connect asynchronous way."""
        if not self._loop:  # pragma: nocover
            raise ValueError("no loop is set for runtime.")

        self.setup_multiplexer()

        self.multiplexer.set_loop(self._loop)
        self.multiplexer.start()
        await self.multiplexer.wait_completed()

    async def _start_agent_loop(self) -> None:
        """Start agent main loop asynchronous way."""
        self.logger.debug("[{}] Runtime started".format(self._agent.name))

        await self.multiplexer.connection_status.wait(ConnectionStates.connected)
        self.logger.debug("[{}] Multiplexer connected.".format(self._agent.name))
        if self.storage:
            await self.storage.wait_connected()
            self.logger.debug("[{}] Storage connected.".format(self._agent.name))

        self.task_manager.start()
        if self._decision_maker is not None:  # pragma: nocover
            self.decision_maker.start()
        self.logger.debug("[{}] Calling setup method...".format(self._agent.name))
        self._agent.setup()
        self.logger.debug("[{}] Run main loop...".format(self._agent.name))
        self.main_loop.start()
        self._state.set(RuntimeStates.running)
        try:
            await self.main_loop.wait_completed()
        except asyncio.CancelledError:
            self.main_loop.stop()
            await self.main_loop.wait_completed()
            raise


class ThreadedRuntime(AsyncRuntime):
    """Run agent and multiplexer in different threads with own asyncio loops."""

    def _get_multiplexer_instance(self) -> AsyncMultiplexer:
        """Create multiplexer instance."""
        return AsyncMultiplexer(self._agent.connections, threaded=True)

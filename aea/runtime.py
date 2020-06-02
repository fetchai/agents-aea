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
import logging
import threading
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from enum import Enum
from typing import Optional

from aea.agent_loop import AsyncState
from aea.helpers.async_utils import ensure_loop
from aea.mail.base import AsyncMultiplexer

if False:
    # for mypy
    from aea.agent import Agent


logger = logging.getLogger(__name__)


class RuntimeStates(Enum):
    """Runtime states."""

    initial = "not_started"
    starting = "starting"
    started = "started"
    stopped = "stopped"


class BaseRuntime(ABC):
    """Abstract runtime class to create implementations."""

    def __init__(
        self, agent: "Agent", loop: Optional[AbstractEventLoop] = None
    ) -> None:
        """
        Init runtime.

        :param agent: Agent to run.
        :param loop: optional event loop. if not provided a new one will be created.
        :return: None
        """
        self._agent: "Agent" = agent
        self._loop = ensure_loop(
            loop
        )  # TODO: decide who constructs loop: agent, runtime, multiplexer.
        self._state: AsyncState = AsyncState(RuntimeStates.initial)

    def start(self) -> None:
        """Start agent using runtime."""
        if self._state.get() is RuntimeStates.started:
            logger.error("Already started!")
            return
        self._start()

    def stop(self) -> None:
        """Stop agent and runtime."""
        logger.debug("Runtime stop called!")
        self.teardown()
        self._stop()
        logger.debug("[{}]: Stopped".format(self._agent.name))

    def teardown(self) -> None:
        """Tear down agent."""
        logger.debug("Runtime teardown ...")
        self._agent.teardown()
        logger.debug("[{}]: Teardown completed".format(self._agent.name))

    @abstractmethod
    def _start(self) -> None:
        """Implement runtime start function here."""
        raise NotImplementedError

    @abstractmethod
    def _stop(self) -> None:
        """Implement runtime stop function here."""
        raise NotImplementedError


class AsyncRuntime(BaseRuntime):
    """Asynchronous runtime: uses asyncio loop for multiplexer and async agent main loop."""

    def __init__(
        self, agent: "Agent", loop: Optional[AbstractEventLoop] = None
    ) -> None:
        """
        Init runtime.

        :param agent: Agent to run.
        :param loop: optional event loop. if not provided a new one will be created.
        :return: None
        """
        super().__init__(agent=agent, loop=loop)
        self._stopping_task: Optional[asyncio.Task] = None
        self._async_stop_lock: Optional[asyncio.Lock] = None

    def _start(self) -> None:
        """Start runtime."""
        try:
            if self._state.get() is RuntimeStates.started:
                raise ValueError("Runtime alrady started!")

            asyncio.set_event_loop(self._loop)
            self._loop.set_debug(True)
            self._agent._multiplexer._loop = self._loop
            self._agent._main_loop._loop = self._loop
            self._state.set(RuntimeStates.started)
            self._thread = threading.current_thread()
            self._async_stop_lock = asyncio.Lock()

            logger.debug(f"Start runtime event loop {self._loop}: {id(self._loop)}")
            self._task = self._loop.create_task(self._start_coro())
            self._loop.run_until_complete(self._task)
            logger.debug("runtime loop stopped!")
            self._stopping_task = None
        except Exception:
            logger.exception("During runtime processing")
            raise

    async def _start_coro(self) -> None:
        """Implmement main loop of runtime."""
        try:
            await self._start_multiplexer()
            self._agent._start_setup()
            await self._agent._main_loop._start_coro()
        except Exception:
            logger.exception("AsyncRuntime exception during run:")
            raise
        finally:
            if self._stopping_task and not self._stopping_task.done():
                await self._stopping_task

    async def _multiplexer_disconnect(self) -> None:
        """Call multiplexer disconnect asynchronous way."""
        await AsyncMultiplexer.disconnect(self._agent._multiplexer)

    async def _start_multiplexer(self) -> None:
        """Call multiplexer connect asynchronous way."""
        await AsyncMultiplexer.connect(self._agent._multiplexer)

    async def _start_agent(self) -> None:
        """Start agent main loop asynchronous way."""
        await self._agent._main_loop._start_coro()

    async def _stop_coro(self) -> None:
        """
        Stop runtime.

        Disconnect multiplexer.
        Tear down agent.
        Stop agent main loop.
        """
        try:
            if self._async_stop_lock is None:
                return  # even not started
            async with self._async_stop_lock:
                if self._state.get() is not RuntimeStates.started:
                    return

                self._agent._main_loop.stop()
                try:
                    await self._agent._main_loop._wait_all_tasks_stopped()
                except BaseException:  # nosec
                    # on stop we do not care about exceptions here, it should be raised in _start.
                    pass  # nosec
                await self._multiplexer_disconnect()
                self._state.set(RuntimeStates.stopped)
        except BaseException:
            logger.exception("AsyncRuntime exception during stop:")
            raise

    def _stop(self) -> None:
        """
        Stop synchronously.

        This one calls async functions and does not guarantee to wait till runtime stopped.
        """
        logger.debug("Stop runtime coroutine.")
        if not self._loop.is_running():
            logger.debug("loop is not running, run stop with event loop!")

            try:
                # dummy spin to cleanup some stuff if it was interrupted
                self._loop.run_until_complete(asyncio.sleep(0.01))
            except BaseException:  # nosec
                pass  # nosec

            self._loop.run_until_complete(self._stop_coro())
            return

        def set_task():
            self._stopping_task = self._loop.create_task(self._stop_coro())

        self._loop.call_soon_threadsafe(set_task)

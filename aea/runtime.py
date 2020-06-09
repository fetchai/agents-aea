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
from aea.multiplexer import AsyncMultiplexer

if False:
    # for mypy
    from aea.agent import Agent


logger = logging.getLogger(__name__)


class RuntimeStates(Enum):
    """Runtime states."""

    initial = "not_started"
    starting = "starting"
    started = "started"
    loop_stopped = "loop_stopped"
    stopping = "stopping"
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
            logger.error("[{}]: Runtime already started".format(self._agent.name))
            return
        self._start()

    def stop(self) -> None:
        """Stop agent and runtime."""
        logger.debug("[{}]: Runtime stopping...".format(self._agent.name))
        self._teardown()
        self._stop()

    def _teardown(self) -> None:
        """Tear down runtime."""
        logger.debug("[{}]: Runtime teardown...".format(self._agent.name))
        self._agent.teardown()
        logger.debug("[{}]: Runtime teardown completed".format(self._agent.name))

    @abstractmethod
    def _start(self) -> None:
        """Implement runtime start function here."""
        raise NotImplementedError

    @abstractmethod
    def _stop(self) -> None:
        """Implement runtime stop function here."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Get running state of the runtime."""
        return self._state.get() == RuntimeStates.started

    @property
    def is_stopped(self) -> bool:
        """Get stopped state of the runtime."""
        return self._state.get() == RuntimeStates.stopped


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
        self._task: Optional[asyncio.Task] = None

    def _start(self) -> None:
        """
        Start runtime synchronously.

        Set event loops for multiplexer and agent run loop.

        Start runtime asynchonously in own event loop.
        """
        if self._state.get() is RuntimeStates.started:
            raise ValueError("Runtime already started!")

        asyncio.set_event_loop(self._loop)
        self._agent._multiplexer.set_loop(self._loop)
        self._agent._main_loop.set_loop(self._loop)

        self._state.set(RuntimeStates.started)

        self._thread = threading.current_thread()
        self._async_stop_lock = asyncio.Lock()

        logger.debug(f"Start runtime event loop {self._loop}: {id(self._loop)}")
        self._task = self._loop.create_task(self._run_runtime())

        try:
            self._loop.run_until_complete(self._task)
            self._state.set(RuntimeStates.loop_stopped)
            logger.debug("Runtime loop stopped!")
        except Exception:
            logger.exception("Exception raised during runtime processing")
            raise
        finally:
            self._stopping_task = None

    async def _run_runtime(self) -> None:
        """Run agent and starts multiplexer."""
        try:
            self._state.set(RuntimeStates.starting)
            await self._start_multiplexer()
            self._agent._start_setup()
            await self._start_agent_loop()
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

    async def _start_agent_loop(self) -> None:
        """Start agent main loop asynchronous way."""
        logger.debug("[{}]: Runtime started".format(self._agent.name))
        self._state.set(RuntimeStates.started)
        await self._agent._main_loop._run_loop()

    async def _stop_runtime(self) -> None:
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

                self._state.set(RuntimeStates.stopping)
                self._agent._main_loop.stop()

                try:
                    await self._agent._main_loop._wait_run_loop_stopped()
                except BaseException:  # nosec
                    # on stop we do not care about exceptions here, it should be raised in _start.
                    pass  # nosec

                self._teardown()

                await self._multiplexer_disconnect()

        except BaseException:
            logger.exception("Runtime exception during stop:")
            raise
        finally:
            self._state.set(RuntimeStates.stopped)
            logger.debug("[{}]: Runtime stopped".format(self._agent.name))

    def _stop(self) -> None:
        """
        Stop synchronously.

        This one calls async functions and does not guarantee to wait till runtime stopped.
        """
        logger.debug("Stop runtime coroutine.")
        if not self._loop.is_running():
            logger.debug(
                "Runtime event loop is not running, start loop with `stop` coroutine"
            )
            try:
                # dummy spin to cleanup some stuff if it was interrupted
                self._loop.run_until_complete(asyncio.sleep(0.01))
            except BaseException:  # nosec
                pass  # nosec

            self._loop.run_until_complete(self._stop_runtime())
            return

        def set_task():
            self._stopping_task = self._loop.create_task(self._stop_runtime())

        self._loop.call_soon_threadsafe(set_task)


class ThreadedRuntime(BaseRuntime):
    """Run agent and multiplexer in different threads with own asyncio loops."""

    def _start(self) -> None:
        """Implement runtime start function here."""
        self._state.set(RuntimeStates.starting)

        self._agent.multiplexer.set_loop(asyncio.new_event_loop())

        self._agent._start_setup()
        self._agent.multiplexer.connect()
        self._start_agent_loop()

    def _start_agent_loop(self) -> None:
        logger.debug("[{}]: Runtime started".format(self._agent.name))
        try:
            self._state.set(RuntimeStates.started)
            self._agent._main_loop.start()
        finally:
            self._state.set(RuntimeStates.loop_stopped)

    def _stop(self) -> None:
        """Implement runtime stop function here."""
        self._state.set(RuntimeStates.stopping)
        self._agent._main_loop.stop()
        self._teardown()
        self._agent.multiplexer.disconnect()
        logger.debug("[{}]: Runtime stopped".format(self._agent.name))
        self._state.set(RuntimeStates.stopped)

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
from abc import ABC, abstractmethod
from asyncio.events import AbstractEventLoop
from contextlib import suppress
from enum import Enum
from typing import Optional, TYPE_CHECKING, cast

from aea.agent_loop import AsyncState
from aea.helpers.async_utils import ensure_loop
from aea.multiplexer import AsyncMultiplexer

if TYPE_CHECKING:  # pragma: nocover
    from aea.agent import Agent


logger = logging.getLogger(__name__)


class RuntimeStates(Enum):
    """Runtime states."""

    starting = "starting"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    error = "error"


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
        self._state: AsyncState = AsyncState(RuntimeStates.stopped, RuntimeStates)
        self._state.add_callback(self._log_runtime_state)
        self._was_started = False

    def _log_runtime_state(self, state) -> None:
        logger.debug(f"[{self._agent.name}]: Runtime state changed to {state}.")

    def start(self) -> None:
        """Start agent using runtime."""
        if self._state.get() is not RuntimeStates.stopped:
            logger.error(
                "[{}]: Runtime is not stopped. Please stop it and start after.".format(
                    self._agent.name
                )
            )
            return
        self._was_started = True
        self._start()

    def stop(self) -> None:
        """Stop agent and runtime."""
        if self._state.get() in (RuntimeStates.stopped, RuntimeStates.stopping):
            logger.error(
                "[{}]: Runtime is already stopped or stopping.".format(self._agent.name)
            )
            return

        logger.debug("[{}]: Runtime stopping...".format(self._agent.name))
        self._teardown()
        self._stop()

    def _teardown(self) -> None:
        """Tear down runtime."""
        logger.debug("[{}]: Runtime teardown...".format(self._agent.name))
        self._agent.teardown()
        logger.debug("[{}]: Runtime teardown completed".format(self._agent.name))

    @abstractmethod
    def _start(self) -> None:  # pragma: nocover
        """Implement runtime start function here."""
        raise NotImplementedError

    @abstractmethod
    def _stop(self) -> None:  # pragma: nocover
        """Implement runtime stop function here."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Get running state of the runtime."""
        return self._state.get() == RuntimeStates.running

    @property
    def is_stopped(self) -> bool:
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
    def state(self) -> RuntimeStates:
        """
        Get runtime state.

        :return: RuntimeStates
        """
        return cast(RuntimeStates, self._state.get())


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

    def set_loop(self, loop: AbstractEventLoop) -> None:
        """
        Set event loop to be used.

        :param loop: event loop to use.
        """
        super().set_loop(loop)
        self._agent.multiplexer.set_loop(self._loop)
        self._agent.main_loop.set_loop(self._loop)
        self._async_stop_lock = asyncio.Lock()

    def _start(self) -> None:
        """
        Start runtime synchronously.

        Set event loops for multiplexer and agent run loop.

        Start runtime asynchonously in own event loop.
        """
        self.set_loop(self._loop)

        logger.debug(f"Start runtime event loop {self._loop}: {id(self._loop)}")
        self._task = self._loop.create_task(self.run_runtime())

        try:
            self._loop.run_until_complete(self._task)
            logger.debug("Runtime loop stopped!")
        except Exception:
            logger.exception("Exception raised during runtime processing")
            self._state.set(RuntimeStates.error)
            raise
        finally:
            self._stopping_task = None

    async def run_runtime(self) -> None:
        """Run agent and starts multiplexer."""
        self._state.set(RuntimeStates.starting)
        try:
            await self._start_multiplexer()
            await self._start_agent_loop()
        except Exception:
            logger.exception("AsyncRuntime exception during run:")
            raise
        finally:
            if self._stopping_task and not self._stopping_task.done():
                await self._stopping_task

    async def _multiplexer_disconnect(self) -> None:
        """Call multiplexer disconnect asynchronous way."""
        await AsyncMultiplexer.disconnect(self._agent.multiplexer)

    async def _start_multiplexer(self) -> None:
        """Call multiplexer connect asynchronous way."""
        self._agent.setup_multiplexer()
        await AsyncMultiplexer.connect(self._agent.multiplexer)

    async def _start_agent_loop(self) -> None:
        """Start agent main loop asynchronous way."""
        logger.debug("[{}]: Runtime started".format(self._agent.name))
        self._agent.start_setup()
        self._state.set(RuntimeStates.running)
        await self._agent.main_loop.run_loop()

    async def _stop_runtime(self) -> None:
        """
        Stop runtime.

        Disconnect multiplexer.
        Tear down agent.
        Stop agent main loop.
        """
        try:
            if self._async_stop_lock is None:  # pragma: nocover
                return  # even not started

            async with self._async_stop_lock:

                if self._state.get() in (
                    RuntimeStates.stopped,
                    RuntimeStates.stopping,
                ):  # pragma: nocover
                    return

                self._state.set(RuntimeStates.stopping)
                self._agent.main_loop.stop()

                with suppress(BaseException):
                    await self._agent.main_loop.wait_run_loop_stopped()

                self._teardown()

                await self._multiplexer_disconnect()

        except BaseException:  # pragma: nocover
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

            with suppress(BaseException):
                self._loop.run_until_complete(asyncio.sleep(0.01))

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

        self._agent.setup_multiplexer()
        self._agent.multiplexer.connect()
        self._agent.start_setup()
        self._start_agent_loop()

    def _start_agent_loop(self) -> None:
        """Start aget's main loop."""
        logger.debug("[{}]: Runtime started".format(self._agent.name))
        try:
            self._state.set(RuntimeStates.running)
            self._agent.main_loop.start()
            logger.debug("[{}]: Runtime stopped".format(self._agent.name))
        except KeyboardInterrupt:  # pragma: nocover
            raise
        except BaseException:  # pragma: nocover
            logger.exception("Runtime exception during stop:")
            self._state.set(RuntimeStates.error)
            raise

    def _stop(self) -> None:
        """Implement runtime stop function here."""
        self._state.set(RuntimeStates.stopping)
        self._agent.main_loop.stop()
        self._teardown()
        self._agent.multiplexer.disconnect()
        logger.debug("[{}]: Runtime stopped".format(self._agent.name))
        self._state.set(RuntimeStates.stopped)

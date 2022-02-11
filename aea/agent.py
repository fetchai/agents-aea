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

"""This module contains the implementation of a generic agent."""
import datetime
import logging
from asyncio import AbstractEventLoop
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from aea.abstract_agent import AbstractAgent
from aea.connections.base import Connection
from aea.exceptions import AEAException
from aea.helpers.logging import WithLogger
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import InBox, OutBox
from aea.runtime import AsyncRuntime, BaseRuntime, RuntimeStates, ThreadedRuntime


_default_logger = logging.getLogger(__name__)


class Agent(AbstractAgent, WithLogger):
    """This class provides an abstract base class for a generic agent."""

    RUNTIMES: Dict[str, Type[BaseRuntime]] = {
        "async": AsyncRuntime,
        "threaded": ThreadedRuntime,
    }
    DEFAULT_RUNTIME: str = "threaded"

    _runtime: BaseRuntime
    _inbox: InBox
    _outbox: OutBox

    def __init__(
        self,
        identity: Identity,
        connections: List[Connection],
        loop: Optional[AbstractEventLoop] = None,
        period: float = 1.0,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        storage_uri: Optional[str] = None,
        logger: Logger = _default_logger,
        task_manager_mode: Optional[str] = None,
    ) -> None:
        """
        Instantiate the agent.

        :param identity: the identity of the agent.
        :param connections: the list of connections of the agent.
        :param loop: the event loop to run the connections.
        :param period: period to call agent's act
        :param loop_mode: loop_mode to choose agent run loop.
        :param runtime_mode: runtime mode to up agent.
        :param storage_uri: optional uri to set generic storage
        :param task_manager_mode: task manager mode.
        :param logger: the logger.
        :param task_manager_mode: mode of the task manager.
        """
        WithLogger.__init__(self, logger=logger)
        self._identity = identity
        self._period = period
        self._tick = 0
        self._runtime_mode = runtime_mode or self.DEFAULT_RUNTIME
        self._task_manager_mode = task_manager_mode
        self._storage_uri = storage_uri

        runtime_class = self._get_runtime_class()

        self._set_runtime_and_mail_boxes(
            runtime_class=runtime_class,
            loop_mode=loop_mode,
            loop=loop,
            multiplexer_options={"connections": connections},
        )

    def _set_runtime_and_mail_boxes(
        self,
        runtime_class: Type[BaseRuntime],
        multiplexer_options: Dict,
        loop_mode: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
    ) -> None:
        """Set the runtime and inbox and outbox."""
        self._runtime = runtime_class(
            agent=self,
            loop_mode=loop_mode,
            loop=loop,
            multiplexer_options=multiplexer_options,
            task_manager_mode=self._task_manager_mode,
        )
        self._inbox = InBox(self.runtime.multiplexer)
        self._outbox = OutBox(self.runtime.multiplexer)

    def _get_runtime_class(self) -> Type[BaseRuntime]:
        """Get runtime class based on runtime mode."""
        if self._runtime_mode not in self.RUNTIMES:
            raise ValueError(
                f"Runtime `{self._runtime_mode} is not supported. valid are: `{list(self.RUNTIMES.keys())}`"
            )
        return self.RUNTIMES[self._runtime_mode]

    @property
    def storage_uri(self) -> Optional[str]:
        """Return storage uri."""
        return self._storage_uri

    @property
    def is_running(self) -> bool:
        """Get running state of the runtime and agent."""
        return self.runtime.is_running

    @property
    def is_stopped(self) -> bool:
        """Get running state of the runtime and agent."""
        return self.runtime.is_stopped

    @property
    def identity(self) -> Identity:
        """Get the identity."""
        return self._identity

    @property
    def inbox(self) -> InBox:  # pragma: nocover
        """
        Get the inbox.

        The inbox contains Envelopes from the Multiplexer.
        The agent can pick these messages for processing.

        :return: InBox instance
        """
        return self._inbox

    @property
    def outbox(self) -> OutBox:  # pragma: nocover
        """
        Get the outbox.

        The outbox contains Envelopes for the Multiplexer.
        Envelopes placed in the Outbox are processed by the Multiplexer.

        :return: OutBox instance
        """
        return self._outbox

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self.identity.name

    @property
    def tick(self) -> int:  # pragma: nocover
        """
        Get the tick or agent loop count.

        Each agent loop (one call to each one of act(), react(), update()) increments the tick.

        :return: tick count
        """
        return self._tick

    @property
    def state(self) -> RuntimeStates:
        """
        Get state of the agent's runtime.

        :return: RuntimeStates
        """
        return self.runtime.state

    @property
    def period(self) -> float:
        """Get a period to call act."""
        return self._period

    @property
    def runtime(self) -> BaseRuntime:
        """Get the runtime."""
        return self._runtime

    def setup(self) -> None:
        """Set up the agent."""
        raise NotImplementedError  # pragma: nocover

    def start(self) -> None:
        """
        Start the agent.

        Performs the following:

        - calls start() on runtime.
        - waits for runtime to complete running (blocking)
        """
        was_started = self.runtime.start()

        if was_started:
            self.runtime.wait_completed(sync=True)
        else:  #  pragma: nocover
            raise AEAException("Failed to start runtime! Was it already started?")

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        """
        raise NotImplementedError  # pragma: nocover

    def act(self) -> None:
        """Perform actions on period."""
        raise NotImplementedError  # pragma: nocover

    def stop(self) -> None:
        """
        Stop the agent.

        Performs the following:

        - calls stop() on runtime
        - waits for runtime to stop (blocking)
        """
        self.runtime.stop()
        self.runtime.wait_completed(sync=True)

    def teardown(self) -> None:
        """Tear down the agent."""
        raise NotImplementedError  # pragma: nocover

    def get_periodic_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        """
        Get all periodic tasks for agent.

        :return: dict of callable with period specified
        """
        return {self.act: (self.period, None)}

    def get_message_handlers(self) -> List[Tuple[Callable[[Any], None], Callable]]:
        """
        Get handlers with message getters.

        :return: List of tuples of callables: handler and coroutine to get a message
        """
        return [
            (self.handle_envelope, self.inbox.async_get),
        ]

    def exception_handler(
        self, exception: Exception, function: Callable
    ) -> bool:  # pragma: nocover
        """
        Handle exception raised during agent main loop execution.

        :param exception: exception raised
        :param function: a callable exception raised in.

        :return: bool, propagate exception if True otherwise skip it.
        """
        self.logger.exception(
            f"Exception {repr(exception)} raised during {repr(function)} call."
        )
        return True

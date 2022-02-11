# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""This module contains the interface definition of the abstract agent."""
import datetime
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

from aea.mail.base import Envelope


class AbstractAgent(ABC):
    """This class provides an abstract base  interface for an agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get agent's name."""

    @property
    @abstractmethod
    def storage_uri(self) -> Optional[str]:
        """Return storage uri."""

    @abstractmethod
    def start(self) -> None:
        """
        Start the agent.

        :return: None
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the agent.

        :return: None
        """

    @abstractmethod
    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """

    @abstractmethod
    def act(self) -> None:
        """
        Perform actions on period.

        :return: None
        """

    @abstractmethod
    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """

    @abstractmethod
    def get_periodic_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        """
        Get all periodic tasks for agent.

        :return: dict of callable with period specified
        """

    @abstractmethod
    def get_message_handlers(self) -> List[Tuple[Callable[[Any], None], Callable]]:
        """
        Get handlers with message getters.

        :return: List of tuples of callables: handler and coroutine to get a message
        """

    @abstractmethod
    def exception_handler(
        self, exception: Exception, function: Callable
    ) -> Optional[bool]:
        """
        Handle exception raised during agent main loop execution.

        :param exception: exception raised
        :param function: a callable exception raised in.

        :return: skip exception if True, otherwise re-raise it
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """

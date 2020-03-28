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

"""The base connection package."""
import logging
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Optional, Set, TYPE_CHECKING, cast

from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ConnectionConfig,
    PublicId,
)
from aea.configurations.components import Component

if TYPE_CHECKING:
    from aea.mail.base import Envelope, Address  # pragma: no cover


logger = logging.getLogger(__name__)


# TODO refactoring: this should be an enum
#      but beware of backward-compatibility.
class ConnectionStatus:
    """The connection status class."""

    def __init__(self):
        """Initialize the connection status."""
        self.is_connected = False  # type: bool
        self.is_connecting = False  # type: bool


class Connection(Component, ABC):
    """Abstract definition of a connection."""

    def __init__(
        self, configuration: ConnectionConfig,
    ):
        """
        Initialize the connection.

        :param configuration: the connection configuration.
        """
        super().__init__(configuration)
        self._loop = None  # type: Optional[AbstractEventLoop]
        self._connection_status = ConnectionStatus()

    @property
    def loop(self) -> Optional[AbstractEventLoop]:
        """Get the event loop."""
        return self._loop

    @loop.setter
    def loop(self, loop: AbstractEventLoop) -> None:
        """
        Set the event loop.

        :param loop: the event loop.
        :return: None
        """
        assert (
            self._loop is None or not self._loop.is_running()
        ), "Cannot set the loop while it is running."
        self._loop = loop

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.CONNECTION

    @property
    def connection_id(self) -> PublicId:
        """Get the id of the connection."""
        return self.public_id

    @property
    def configuration(self) -> ConnectionConfig:
        """Get the connection configuration."""
        return cast(ConnectionConfig, super().configuration)

    @property
    def restricted_to_protocols(self) -> Set[PublicId]:
        """Get the restricted to protocols.."""
        return self._configuration.restricted_to_protocols

    @property
    def excluded_protocols(self) -> Set[PublicId]:
        """Get the restricted to protocols.."""
        return self._configuration.excluded_protocols

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get the connection status."""
        return self._connection_status

    @abstractmethod
    async def connect(self):
        """Set up the connection."""

    @abstractmethod
    async def disconnect(self):
        """Tear down the connection."""

    @abstractmethod
    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """

    @abstractmethod
    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :return: the received envelope, or None if an error occurred.
        """

    @classmethod
    def load_from_directory(
        cls, component_type: ComponentType, directory: Path
    ) -> "Component":
        pass

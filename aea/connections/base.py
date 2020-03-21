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
        self,
        connection_id: Optional[PublicId] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Initialize the connection.

        :param connection_id: the connection identifier.
        :param restricted_to_protocols: the set of protocols ids of the only supported protocols for this connection.
        :param excluded_protocols: the set of protocols ids that we want to exclude for this connection.
        """
        # TODO for backward compatibility, the configuration attribute will be set after initialization
        super().__init__(cast(ComponentConfiguration, None))
        # TODO connection id can be removed
        if connection_id is None:
            raise ValueError("Connection public id is a mandatory argument.")
        self._connection_id = connection_id
        self._restricted_to_protocols = self._get_restricted_to_protocols(
            restricted_to_protocols
        )
        self._excluded_protocols = self._get_excluded_protocols(excluded_protocols)

        self._loop = None  # type: Optional[AbstractEventLoop]
        self._connection_status = ConnectionStatus()

    def _get_restricted_to_protocols(
        self, restricted_to_protocols: Optional[Set[PublicId]] = None
    ) -> Set[PublicId]:
        if restricted_to_protocols is not None:
            return restricted_to_protocols
        # never gonna reach next condition cause isinstance check will fail comparing type 'set' to type 'property'
        # TODO: investigate and fix that
        elif hasattr(type(self), "restricted_to_protocols") and isinstance(
            getattr(type(self), "restricted_to_protocols"), set
        ):  # pragma: no cover
            return getattr(type(self), "restricted_to_protocols")
        else:
            return set()

    def _get_excluded_protocols(
        self, excluded_protocols: Optional[Set[PublicId]] = None
    ) -> Set[PublicId]:
        if excluded_protocols is not None:
            return excluded_protocols
        # never gonna reach next condition cause isinstance check will fail comparing type 'set' to type 'property'
        # TODO: investigate and fix that
        elif hasattr(type(self), "excluded_protocols") and isinstance(
            getattr(type(self), "excluded_protocols"), set
        ):  # pragma: no cover
            return getattr(type(self), "excluded_protocols")
        else:
            return set()

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
        return self._connection_id

    @property
    def restricted_to_protocols(self) -> Set[PublicId]:
        """Get the restricted to protocols.."""
        # TODO refactor __init__
        if self.configuration is None:
            return self._restricted_to_protocols
        else:
            connection_configuration = cast(ConnectionConfig, self.configuration)
            return connection_configuration.restricted_to_protocols

    @property
    def excluded_protocols(self) -> Set[PublicId]:
        """Get the restricted to protocols.."""
        if self.configuration is None:
            return self._excluded_protocols
        else:
            connection_configuration = cast(ConnectionConfig, self.configuration)
            return connection_configuration.excluded_protocols

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
    @abstractmethod
    def from_config(
        cls, address: "Address", connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Initialize a connection instance from a configuration.

        :param address: the address of the agent.
        :param connection_configuration: the connection configuration.
        :return: an instance of the concrete connection class.
        """

    @classmethod
    def load_from_directory(
        cls, component_type: ComponentType, directory: Path
    ) -> "Component":
        pass

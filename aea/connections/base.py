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
from abc import abstractmethod, ABC
from asyncio import AbstractEventLoop
from typing import TYPE_CHECKING, Optional, Set

from aea.configurations.base import ConnectionConfig

if TYPE_CHECKING:
    from aea.mail.base import Envelope, Address  # pragma: no cover


logger = logging.getLogger(__name__)


class ConnectionStatus(object):
    """The connection status class."""

    def __init__(self):
        """Initialize the connection status."""
        self.is_connected = False


class Connection(ABC):
    """Abstract definition of a connection."""

    def __init__(self, connection_id: str, restricted_to_protocols: Optional[Set[str]] = None):
        """
        Initialize the connection.

        :param connection_id: the connection identifier.
        :param restricted_to_protocols: the set of protocols ids of the only supported protocols for this connection.
        """
        self._connection_id = connection_id
        self._restricted_to_protocols = self._get_restricted_to_protocols(restricted_to_protocols)

        self._loop = None  # type: Optional[AbstractEventLoop]
        self._connection_status = ConnectionStatus()

    def _get_restricted_to_protocols(self, restricted_to_protocols: Optional[Set[str]] = None) -> Set[str]:
        if restricted_to_protocols is not None:
            return restricted_to_protocols
        elif hasattr(type(self), "restricted_to_protocols") and isinstance(getattr(type(self), "restricted_to_protocols"), set):
            return getattr(type(self), "restricted_to_protocols")
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
        assert self._loop is None or not self._loop.is_running(), "Cannot set the loop while it is running."
        self._loop = loop

    @property
    def connection_id(self) -> str:
        """Get the id of the connection."""
        return self._connection_id

    @property
    def restricted_to_protocols(self) -> Set[str]:
        """Get the restricted to protocols.."""
        return self._restricted_to_protocols

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
    async def send(self, envelope: 'Envelope') -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """

    @abstractmethod
    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope.

        :return: the received envelope, or None if an error occurred.
        """

    @classmethod
    @abstractmethod
    def from_config(cls, address: 'Address', connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Initialize a connection instance from a configuration.

        :param address: the address of the agent.
        :param connection_configuration: the connection configuration.
        :return: an instance of the concrete connection class.
        """

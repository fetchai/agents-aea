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

from abc import abstractmethod, ABC
from queue import Queue
from typing import Optional, TYPE_CHECKING

from aea.configurations.base import ConnectionConfig
if TYPE_CHECKING:
    from aea.mail.base import Envelope  # pragma: no cover


class Channel(ABC):
    """Abstract definition of a channel."""

    @abstractmethod
    def connect(self) -> Optional[Queue]:
        """
        Set up the connection.

        :return: A queue or None.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Tear down the connection.

        :return: None.
        """

    @abstractmethod
    def send(self, envelope: 'Envelope') -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """

    def receive(self) -> None:
        """
        Receives an envelope.

        :return: None.
        """


class ConnectionStatus(object):
    """The connection status class."""

    def __init__(self):
        """Initialize the connection status."""
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if the connection is established."""
        return self._is_connected

    @is_connected.setter
    def is_connected(self, is_connected: bool) -> None:
        self._is_connected = is_connected


class Connection(ABC):
    """Abstract definition of a connection."""

    channel: Channel

    def __init__(self):
        """Initialize the connection."""
        self.in_queue = Queue()
        self.out_queue = Queue()
        self._connection_status = ConnectionStatus()

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get the connection status."""
        return self._connection_status

    @abstractmethod
    def connect(self):
        """Set up the connection."""

    @abstractmethod
    def disconnect(self):
        """Tear down the connection."""

    @abstractmethod
    def send(self, envelope: 'Envelope'):
        """Send a message."""

    @classmethod
    @abstractmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Initialize a connection instance from a configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration.
        :return: an instance of the concrete connection class.
        """

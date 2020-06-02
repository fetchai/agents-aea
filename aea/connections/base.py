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


from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from typing import Optional, Set, TYPE_CHECKING, cast

from aea.components.base import Component
from aea.configurations.base import (
    ComponentType,
    ConnectionConfig,
    PublicId,
)
from aea.components.base import Component
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity


if TYPE_CHECKING:
    from aea.mail.base import Envelope, Address  # pragma: no cover


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
        configuration: Optional[ConnectionConfig] = None,
        identity: Optional[Identity] = None,
        cryptos: Optional[CryptoStore] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
        connection_id: Optional[PublicId] = None,
    ):
        """
        Initialize the connection.

        The configuration must be specified if and only if the following
        parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

        :param configuration: the connection configuration.
        :param identity: the identity object held by the agent.
        :param cryptos: the crypto store for encrypted communication.
        :param restricted_to_protocols: the set of protocols ids of the only supported protocols for this connection.
        :param excluded_protocols: the set of protocols ids that we want to exclude for this connection.
        :param connection_id: the connection identifier.
        """
        super().__init__(configuration)
        self._loop: Optional[AbstractEventLoop] = None
        self._connection_status = ConnectionStatus()

        self._identity: Optional[Identity] = identity
        self._cryptos: CryptoStore = cryptos if cryptos is not None else CryptoStore()

        self._restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self._excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )
        self._connection_id = connection_id
        assert (self._connection_id is None) is not (
            self._configuration is None
        ), "Either provide the configuration or the connection id."

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
    def address(self) -> "Address":
        """Get the address."""
        assert (
            self._identity is not None
        ), "You must provide the identity in order to retrieve the address."
        return self._identity.address

    @property
    def cryptos(self) -> CryptoStore:
        """Get the crypto store."""
        return self._cryptos

    @property
    def component_type(self) -> ComponentType:
        """Get the component type."""
        return ComponentType.CONNECTION

    @property
    def connection_id(self) -> PublicId:
        """Get the id of the connection."""
        if self._configuration is None:
            return cast(PublicId, self._connection_id)
        else:
            return super().public_id

    @property
    def configuration(self) -> ConnectionConfig:
        """Get the connection configuration."""
        assert self._configuration is not None, "Configuration not set."
        return cast(ConnectionConfig, super().configuration)

    @property
    def restricted_to_protocols(self) -> Set[PublicId]:
        if self._configuration is None:
            return self._restricted_to_protocols
        else:
            return self.configuration.restricted_to_protocols

    @property
    def excluded_protocols(self) -> Set[PublicId]:
        """Get the ids of the excluded protocols for this connection."""
        if self._configuration is None:
            return self._excluded_protocols
        else:
            return self.configuration.excluded_protocols

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
    def from_config(
        cls, configuration: ConnectionConfig, identity: Identity, cryptos: CryptoStore
    ) -> "Connection":
        """
        Initialize a connection instance from a configuration.

        :param configuration: the connection configuration.
        :param identity: the identity object.
        :param cryptos: object to access the connection crypto objects.
        :return: an instance of the concrete connection class.
        """
        return cls(configuration=configuration, identity=identity, cryptos=cryptos)

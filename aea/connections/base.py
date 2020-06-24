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
import inspect
import logging
import re
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from pathlib import Path
from typing import Optional, Set, TYPE_CHECKING, cast

from aea.components.base import Component
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ConnectionConfig,
    PublicId,
)
from aea.crypto.wallet import CryptoStore
from aea.helpers.base import load_aea_package, load_module
from aea.identity.base import Identity


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

    connection_id = None  # type: PublicId

    def __init__(
        self,
        configuration: ConnectionConfig,
        identity: Optional[Identity] = None,
        crypto_store: Optional[CryptoStore] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
        excluded_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Initialize the connection.

        The configuration must be specified if and only if the following
        parameters are None: connection_id, excluded_protocols or restricted_to_protocols.

        :param configuration: the connection configuration.
        :param identity: the identity object held by the agent.
        :param crypto_store: the crypto store for encrypted communication.
        :param restricted_to_protocols: the set of protocols ids of the only supported protocols for this connection.
        :param excluded_protocols: the set of protocols ids that we want to exclude for this connection.
        """
        assert configuration is not None, "The configuration must be provided."
        super().__init__(configuration)
        assert (
            super().public_id == self.connection_id
        ), "Connection ids in configuration and class not matching."
        self._loop: Optional[AbstractEventLoop] = None
        self._connection_status = ConnectionStatus()

        self._identity = identity
        self._crypto_store = crypto_store

        self._restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self._excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )

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
    def address(self) -> "Address":  # pragma: nocover
        """Get the address."""
        assert (
            self._identity is not None
        ), "You must provide the identity in order to retrieve the address."
        return self._identity.address

    @property
    def crypto_store(self) -> CryptoStore:  # pragma: nocover
        """Get the crypto store."""
        assert self._crypto_store is not None, "CryptoStore not available."
        return self._crypto_store

    @property
    def has_crypto_store(self) -> bool:  # pragma: nocover
        """Check if the connection has the crypto store."""
        return self._crypto_store is not None

    @property
    def component_type(self) -> ComponentType:  # pragma: nocover
        """Get the component type."""
        return ComponentType.CONNECTION

    @property
    def configuration(self) -> ConnectionConfig:
        """Get the connection configuration."""
        assert self._configuration is not None, "Configuration not set."
        return cast(ConnectionConfig, super().configuration)

    @property
    def restricted_to_protocols(self) -> Set[PublicId]:  # pragma: nocover
        """Get the ids of the protocols this connection is restricted to."""
        if self._configuration is None:
            return self._restricted_to_protocols
        else:
            return self.configuration.restricted_to_protocols

    @property
    def excluded_protocols(self) -> Set[PublicId]:  # pragma: nocover
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
    def from_dir(
        cls, directory: str, identity: Identity, crypto_store: CryptoStore
    ) -> "Connection":
        """
        Load the connection from a directory.

        :param directory: the directory to the connection package.
        :param identity: the identity object.
        :param crypto_store: object to access the connection crypto objects.
        :return: the connection object.
        """
        configuration = cast(
            ConnectionConfig,
            ComponentConfiguration.load(ComponentType.CONNECTION, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Connection.from_config(configuration, identity, crypto_store)

    @classmethod
    def from_config(
        cls,
        configuration: ConnectionConfig,
        identity: Identity,
        crypto_store: CryptoStore,
    ) -> "Connection":
        """
        Load a connection from a configuration.

        :param configuration: the connection configuration.
        :param identity: the identity object.
        :param crypto_store: object to access the connection crypto objects.
        :return: an instance of the concrete connection class.
        """
        configuration = cast(ConnectionConfig, configuration)
        directory = cast(Path, configuration.directory)
        load_aea_package(configuration)
        connection_module_path = directory / "connection.py"
        assert (
            connection_module_path.exists() and connection_module_path.is_file()
        ), "Connection module '{}' not found.".format(connection_module_path)
        connection_module = load_module(
            "connection_module", directory / "connection.py"
        )
        classes = inspect.getmembers(connection_module, inspect.isclass)
        connection_class_name = cast(str, configuration.class_name)
        connection_classes = list(
            filter(lambda x: re.match(connection_class_name, x[0]), classes)
        )
        name_to_class = dict(connection_classes)
        logger.debug("Processing connection {}".format(connection_class_name))
        connection_class = name_to_class.get(connection_class_name, None)
        assert connection_class is not None, "Connection class '{}' not found.".format(
            connection_class_name
        )
        return connection_class(
            configuration=configuration, identity=identity, crypto_store=crypto_store
        )

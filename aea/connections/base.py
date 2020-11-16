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
import asyncio
import inspect
import re
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Generator, Optional, Set, TYPE_CHECKING, cast

from aea.components.base import Component, load_aea_package
from aea.configurations.base import ComponentType, ConnectionConfig, PublicId
from aea.configurations.loader import load_component_configuration
from aea.crypto.wallet import CryptoStore
from aea.exceptions import (
    AEAComponentLoadException,
    AEAInstantiationException,
    enforce,
    parse_exception,
)
from aea.helpers.async_utils import AsyncState
from aea.helpers.base import load_module
from aea.helpers.logging import get_logger
from aea.identity.base import Identity


if TYPE_CHECKING:
    from aea.mail.base import Address, Envelope  # pragma: no cover


class ConnectionStates(Enum):
    """Connection states enum."""

    connected = "connected"
    connecting = "connecting"
    disconnecting = "disconnecting"
    disconnected = "disconnected"


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
        **kwargs,
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
        enforce(configuration is not None, "The configuration must be provided.")
        super().__init__(configuration, **kwargs)
        enforce(
            super().public_id == self.connection_id,
            "Connection ids in configuration and class not matching.",
        )
        self._state = AsyncState(ConnectionStates.disconnected)

        self._identity = identity
        self._crypto_store = crypto_store

        self._restricted_to_protocols = (
            restricted_to_protocols if restricted_to_protocols is not None else set()
        )
        self._excluded_protocols = (
            excluded_protocols if excluded_protocols is not None else set()
        )

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop."""
        enforce(asyncio.get_event_loop().is_running(), "Event loop is not running.")
        return asyncio.get_event_loop()

    def _ensure_connected(self) -> None:  # pragma: nocover
        """Raise exception if connection is not connected."""
        if not self.is_connected:
            raise ConnectionError("Connection is not connected! Connect first!")

    @staticmethod
    def _ensure_valid_envelope_for_external_comms(envelope: "Envelope") -> None:
        """
        Ensure the envelope sender and to are valid addresses for agent-to-agent communication.

        :param envelope: the envelope
        """
        enforce(
            not envelope.is_sender_public_id,
            f"Sender field of envelope is public id, needs to be address. Found={envelope.sender}",
        )
        enforce(
            not envelope.is_to_public_id,
            f"To field of envelope is public id, needs to be address. Found={envelope.to}",
        )

    @contextmanager
    def _connect_context(self) -> Generator:
        """Set state connecting, disconnecteing, dicsconnected during connect method."""
        with self._state.transit(
            initial=ConnectionStates.connecting,
            success=ConnectionStates.connected,
            fail=ConnectionStates.disconnected,
        ):
            yield

    @property
    def address(self) -> "Address":  # pragma: nocover
        """Get the address."""
        if self._identity is None:
            raise ValueError(
                "You must provide the identity in order to retrieve the address."
            )
        return self._identity.address

    @property
    def crypto_store(self) -> CryptoStore:  # pragma: nocover
        """Get the crypto store."""
        if self._crypto_store is None:
            raise ValueError("CryptoStore not available.")
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
        if self._configuration is None:  # pragma: nocover
            raise ValueError("Configuration not set.")
        return cast(ConnectionConfig, super().configuration)

    @property
    def restricted_to_protocols(self) -> Set[PublicId]:  # pragma: nocover
        """Get the ids of the protocols this connection is restricted to."""
        if self._configuration is None:
            return self._restricted_to_protocols
        return self.configuration.restricted_to_protocols

    @property
    def excluded_protocols(self) -> Set[PublicId]:  # pragma: nocover
        """Get the ids of the excluded protocols for this connection."""
        if self._configuration is None:
            return self._excluded_protocols
        return self.configuration.excluded_protocols

    @property
    def state(self) -> ConnectionStates:
        """Get the connection status."""
        return self._state.get()

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
        cls, directory: str, identity: Identity, crypto_store: CryptoStore, **kwargs
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
            load_component_configuration(ComponentType.CONNECTION, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Connection.from_config(configuration, identity, crypto_store, **kwargs)

    @classmethod
    def from_config(
        cls,
        configuration: ConnectionConfig,
        identity: Identity,
        crypto_store: CryptoStore,
        **kwargs,
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
        if not (connection_module_path.exists() and connection_module_path.is_file()):
            raise AEAComponentLoadException(
                "Connection module '{}' not found.".format(connection_module_path)
            )
        connection_module = load_module(
            "connection_module", directory / "connection.py"
        )
        classes = inspect.getmembers(connection_module, inspect.isclass)
        connection_class_name = cast(str, configuration.class_name)
        connection_classes = list(
            filter(lambda x: re.match(connection_class_name, x[0]), classes)
        )
        name_to_class = dict(connection_classes)
        logger = get_logger(__name__, identity.name)
        logger.debug("Processing connection {}".format(connection_class_name))
        connection_class = name_to_class.get(connection_class_name, None)
        if connection_class is None:
            raise AEAComponentLoadException(
                "Connection class '{}' not found.".format(connection_class_name)
            )
        try:
            connection = connection_class(
                configuration=configuration,
                identity=identity,
                crypto_store=crypto_store,
                **kwargs,
            )
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            e_str = parse_exception(e)
            raise AEAInstantiationException(
                f"An error occured during instantiation of connection {configuration.public_id}/{configuration.class_name}:\n{e_str}"
            )
        return connection

    @property
    def is_connected(self) -> bool:  # pragma: nocover
        """Return is connected state."""
        return self.state == ConnectionStates.connected

    @property
    def is_connecting(self) -> bool:  # pragma: nocover
        """Return is connecting state."""
        return self.state == ConnectionStates.connecting

    @property
    def is_disconnected(self) -> bool:  # pragma: nocover
        """Return is disconnected state."""
        return self.state == ConnectionStates.disconnected

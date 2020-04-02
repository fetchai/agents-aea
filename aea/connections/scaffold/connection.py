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

"""Scaffold connection and channel."""

from typing import Optional

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope, Address


class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    def __init__(self, configuration: ConnectionConfig, address: Address):
        """
        Initialize a connection to an SDK or API.

        :param configuration: the connection configuration.
        :param address: the address used in the protocols.
        """
        super().__init__(configuration=configuration, address=address)

    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def from_config(
        cls, connection_configuration: ConnectionConfig, address: Address
    ) -> "Connection":
        """
        Get the scaffold connection from the connection configuration.

        :param connection_configuration: the connection configuration object.
        :param address: the address of the agent.
        :return: the connection object
        """
        return MyScaffoldConnection(connection_configuration, address)

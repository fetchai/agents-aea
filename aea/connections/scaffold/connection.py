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

import logging
from typing import Optional

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope

logger = logging.getLogger(__name__)


class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    def __init__(self, connection_id: str, public_key: str, *args, **kwargs):
        """
        Initialize a connection to an SDK or API.

        :param public_key: the public key used in the protocols.
        """
        super().__init__(connection_id)
        self.public_key = public_key

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

    async def send(self, envelope: 'Envelope') -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the Gym connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        raise NotImplementedError  # pragma: no cover

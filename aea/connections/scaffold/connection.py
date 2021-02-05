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

from aea.configurations.base import PublicId
from aea.connections.base import BaseSyncConnection, Connection
from aea.mail.base import Envelope


"""
Choose one of the possible implementations:

Sync (inherited from BaseSyncConnection) or Async (inherited from Connection) connection and remove unused one.
"""


class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PublicId.from_str("fetchai/scaffold:0.1.0")

    def __init__(self, **kwargs):
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
        super().__init__(**kwargs)  # pragma: no cover

    async def connect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        raise NotImplementedError  # pragma: no cover

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    async def receive(self, *args, **kwargs) -> Optional[Envelope]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        raise NotImplementedError  # pragma: no cover


class MyScaffoldSyncConnection(BaseSyncConnection):
    """Proxy to the functionality of the SDK or API."""

    MAX_WORKER_THREADS = 5

    connection_id = PublicId.from_str("fetchai/sync_scaffold:0.1.0")

    def __init__(self, *args, **kwargs):
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
        super().__init__(*args, **kwargs)
        raise NotImplementedError  # pragma: no cover

    def main(self):
        """Run main."""
        raise NotImplementedError  # pragma: no cover

    def on_send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None.
        """
        raise NotImplementedError  # pragma: no cover

    def on_connect(self):
        """
        Tear down the connection.

        Connection status set automatically.
        """
        raise NotImplementedError  # pragma: no cover

    def on_disconnect(self):
        """
        Tear down the connection.

        Connection status set automatically.
        """
        raise NotImplementedError  # pragma: no cover

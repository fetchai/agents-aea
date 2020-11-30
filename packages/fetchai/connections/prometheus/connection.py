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

"""Prometheus connection and channel."""

from typing import Optional, cast

from prometheus_client import start_http_server

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel


class PrometheusDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The server connection maintains the dialogue on behalf of the client
            return BaseDialogue.Role.

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            **kwargs,
        )

class PrometheusConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PublicId.from_str("fetchai/prometheus:0.1.0")

    def __init__(self, **kwargs):
        """
        Initialize a connection to prometheus.

        :param configuration: the connection configuration.
        :param crypto_store: object to access the connection crypto objects.
        :param identity: the identity object.
        """
        super().__init__(**kwargs)
        self._port = cast(int, self.configuration.config.get("port"))


    async def connect(self) -> None:
        """
        Set up the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        if self.is_connected:
            return

        self.logger.info("Starting up the prometheus connection...")
        self._state.set(ConnectionStates.connecting)
        start_http_server(self._port)
        self.logger.info(f"Successfully started prometheus connection at port: {self._port}")
        self._state.set(ConnectionStates.connected)


    async def disconnect(self) -> None:
        """
        Tear down the connection.

        In the implementation, remember to update 'connection_status' accordingly.
        """
        pass  # pragma: no cover

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        pass  # pragma: no cover

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        self.logger.info("Received something to the prometheus connection...")



        pass  # pragma: no cover

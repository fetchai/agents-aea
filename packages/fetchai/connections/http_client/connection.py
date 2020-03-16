# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""HTTP client connection and channel"""

import asyncio
import logging
from asyncio import CancelledError
from typing import Optional, Set, cast

import requests

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500

logger = logging.getLogger(__name__)

RequestId = str


class HTTPClientChannel:
    """A wrapper for a HTTPClient for a RESTful API."""

    def __init__(
        self,
        agent_address: Address,
        address: str,
        port: int,
        excluded_protocols: Optional[Set[PublicId]] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Initialize a channel and process the initial API specification from the file path (if given).

        :param agent_address: the address of the agent.
        :param address: RESTful API hostname / IP address
        :param port: RESTful API port number
        :param excluded_protocols: this connection cannot handle messages adhering to any of the protocols in this set
        :param restricted_to_protocols: this connection can only handle messages adhering to protocols in this set
        """
        self.agent_address = agent_address
        self.address = address
        self.port = port
        self.restricted_to_protocols = restricted_to_protocols
        self.in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]  # pragma: no cover
        self.excluded_protocols = excluded_protocols
        self.is_stopped = True
        logger.info("Initialised the HTTP client channel")

    def connect(self):
        """Connect."""
        if self.is_stopped:
            self.is_stopped = False
            try:
                logger.info(self.address)
                response = requests.request(
                    method="GET", url=f"http://{self.address}:{self.port}/status"
                )
                logger.debug("Status code is: {}".format(response.status_code))
                assert response.status_code == 200, "Connection failed."
            except Exception as e:  # pragma: no cover
                logger.warning(str(e))
                raise

    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope as a HTTP request, wait for its response, translate the response into an envelop, and sent it back to the agent.

        :param envelope: the envelope
        :return: None
        """
        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the oef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")

            if envelope is not None:
                http_message = cast(
                    HttpMessage, HttpSerializer().decode(envelope.message)
                )
                if http_message.performative == HttpMessage.Performative.REQUEST:
                    response = requests.request(
                        method=http_message.method,
                        url=http_message.url,
                        headers=http_message.headers,
                        data=http_message.bodyy,
                    )
                    envelope = self.to_envelope(response)
                    self.loop.call_soon_threadsafe(self.in_queue.put_nowait, envelope)
                else:
                    raise ValueError("The HTTPMessage performative must be a REQUEST.")
            else:
                raise ValueError("The Envelop object to be sent is None.")

    def to_envelope(self, http_response: requests.models.Response) -> Envelope:
        """
        Process HTTP response by packaging it into an Envelope and sending it to in-queue.

        :param http_response: the http response object
        """

        # uri = URI(self.full_url_pattern)
        # context = EnvelopeContext(connection_id=connection_id, uri=uri)
        http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.RESPONSE,
            status_code=http_response.status_code,
            headers=http_response.headers,
            status_text=http_response.reason,
            bodyy=http_response.content if http_response.content is not None else b"",
            version="",
        )
        envelope = Envelope(
            to=self.agent_address,
            sender="HTTP server",
            protocol_id=PublicId.from_str("fetchai/http:0.1.0"),
            # context=context,
            message=HttpSerializer().encode(http_message),
        )
        return envelope

    def disconnect(self) -> None:
        """
        Disconnect.

        Join the thread, then stop the channel.
        """
        if not self.is_stopped:
            logger.info(f"HTTP Client has shutdown on port: {self.port}.")
            self.is_stopped = True


class HTTPClientConnection(Connection):
    """Proxy to the functionality of the web RESTful API."""

    def __init__(
        self,
        agent_address: Address,
        provider_address: str,
        provider_port: int,
        *args,
        **kwargs,
    ):
        """
        Initialize a connection to a RESTful API.

        :param agent_address: the address of the agent.
        :param provider_address: RESTful API hostname / IP address
        :param provider_port: RESTful API port number
        """

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http_client", "0.1.0")

        super().__init__(*args, **kwargs)
        self.agent_address = agent_address
        self.channel = HTTPClientChannel(
            agent_address,
            provider_address,
            provider_port,
            excluded_protocols=self.excluded_protocols,
            restricted_to_protocols=kwargs.get("restricted_to_protocols", {}),
        )

    async def connect(self) -> None:
        """
        Connect to a HTTP server.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.connection_status.is_connected = True
            self.channel.in_queue = asyncio.Queue()
            self.channel.loop = self.loop
            self.channel.connect()

    async def disconnect(self) -> None:
        """
        Disconnect from a HTTP server.

        :return: None
        """
        if self.connection_status.is_connected:
            self.connection_status.is_connected = False
            self.channel.disconnect()

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        if not self.connection_status.is_connected:
            raise ConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )  # pragma: no cover
        self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :return: the envelope received, or None.
        """
        if not self.connection_status.is_connected:
            raise ConnectionError(
                "Connection not established yet. Please use 'connect()'."
            )  # pragma: no cover
        assert self.channel.in_queue is not None
        try:
            envelope = await self.channel.in_queue.get()
            if envelope is None:
                return None  # pragma: no cover
            return envelope
        except CancelledError:  # pragma: no cover
            return None

    @classmethod
    def from_config(
        cls, agent_address: Address, connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from the connection configuration.

        :param agent_address: the address of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        address = cast(str, connection_configuration.config.get("address"))
        port = cast(int, connection_configuration.config.get("port"))
        restricted_to_protocols_names = {
            p.name for p in connection_configuration.restricted_to_protocols
        }
        excluded_protocols_names = {
            p.name for p in connection_configuration.excluded_protocols
        }
        return HTTPClientConnection(
            agent_address,
            address,
            port,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )

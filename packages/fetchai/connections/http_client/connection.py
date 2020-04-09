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
import json
import logging
from asyncio import CancelledError
from typing import Optional, Set, Union, cast

from aiohttp import web

import requests


from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500

logger = logging.getLogger("aea.packages.fetchai.connections.http_client")

RequestId = str


class HTTPClientChannel:
    """A wrapper for a HTTPClient."""

    def __init__(
        self,
        agent_address: Address,
        address: str,
        port: int,
        connection_id: PublicId,
        excluded_protocols: Optional[Set[PublicId]] = None,
        restricted_to_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Initialize an http client channel.

        :param agent_address: the address of the agent.
        :param address: server hostname / IP address
        :param port: server port number
        :param excluded_protocols: this connection cannot handle messages adhering to any of the protocols in this set
        :param restricted_to_protocols: this connection can only handle messages adhering to protocols in this set
        """
        self.agent_address = agent_address
        self.address = address
        self.port = port
        self.connection_id = connection_id
        self.restricted_to_protocols = restricted_to_protocols
        self.in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self.loop = (
            None
        )  # type: Optional[asyncio.AbstractEventLoop]  # pragma: no cover
        self.excluded_protocols = excluded_protocols
        self.is_stopped = True
        logger.info("Initialised the HTTP client channel")

    def connect(self):
        """Connect."""
        pass

    def send(self, request_envelope: Envelope) -> None:
        """
        Convert an http envelope into an http request, send the http request, wait for and receive its response, translate the response into a response envelop,
        and send the response envelope to the in-queue.

        :param request_envelope: the envelope containing an http request
        :return: None
        """
        if self.excluded_protocols is not None:
            if request_envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the http client connection: protocol_id={}".format(
                        request_envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")

            if request_envelope is not None:
                request_http_message = cast(
                    HttpMessage, HttpSerializer().decode(request_envelope.message)
                )
                if (
                    request_http_message.performative
                    == HttpMessage.Performative.REQUEST
                ):
                    response = requests.request(
                        method=request_http_message.method,
                        url=request_http_message.url,
                        headers=request_http_message.headers,
                        data=request_http_message.bodyy,
                    )
                    response_envelope = self.to_envelope(
                        self.connection_id, request_http_message, response
                    )
                    self.in_queue.put_nowait(response_envelope)  # type: ignore
                else:
                    logger.warning(
                        "The HTTPMessage performative must be a REQUEST. Envelop dropped."
                    )

    def to_envelope(
        self,
        connection_id: PublicId,
        http_request_message: HttpMessage,
        http_response: requests.models.Response,
    ) -> Envelope:
        """
        Convert an HTTP response object (from the 'requests' library) into an Envelope containing an HttpMessage (from the 'http' Protocol).

        :param connection_id: the connection id
        :param http_request_message: the message of the http request envelop
        :param http_response: the http response object
        """

        context = EnvelopeContext(connection_id=connection_id)
        http_message = HttpMessage(
            dialogue_reference=http_request_message.dialogue_reference,
            target=http_request_message.target,
            message_id=http_request_message.message_id,
            performative=HttpMessage.Performative.RESPONSE,
            status_code=http_response.status_code,
            headers=json.dumps(dict(http_response.headers)),
            status_text=http_response.reason,
            bodyy=http_response.content if http_response.content is not None else b"",
            version="",
        )
        envelope = Envelope(
            to=self.agent_address,
            sender="HTTP Server",
            protocol_id=PublicId.from_str("fetchai/http:0.1.0"),
            context=context,
            message=HttpSerializer().encode(http_message),
        )
        return envelope

    def disconnect(self) -> None:
        """Disconnect."""
        if not self.is_stopped:
            logger.info("HTTP Client has shutdown on port: {}.".format(self.port))
            self.is_stopped = True


class HTTPClientConnection(Connection):
    """Proxy to the functionality of the web client."""

    def __init__(
        self, provider_address: str, provider_port: int, **kwargs,
    ):
        """
        Initialize a connection.

        :param provider_address: server hostname / IP address
        :param provider_port: server port number
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http_client", "0.1.0")

        super().__init__(**kwargs)
        self.channel = HTTPClientChannel(
            self.address,
            provider_address,
            provider_port,
            connection_id=self.connection_id,
            excluded_protocols=self.excluded_protocols,
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

    async def receive(self, *args, **kwargs) -> Optional[Union["Envelope", None]]:
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
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from a connection configuration.

        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        provider_address = cast(str, configuration.config.get("address"))
        provider_port = cast(int, configuration.config.get("port"))
        return HTTPClientConnection(
            provider_address,
            provider_port,
            address=address,
            configuration=configuration,
        )


class WebhookChannel:
    """A wrapper for a Webhook."""

    def __init__(
        self,
        agent_address: Address,
        webhook_address: Address,
        webhook_port: int,
        # webhook_host: Address,
        connection_id: PublicId,
    ):
        """
        Initialize a webhook channel.

        :param agent_address: the address of the agent
        :param webhook_address: webhook hostname / IP address
        :param webhook_port: webhook port number
        :param connection_id: the connection id
        """
        self.agent_address = agent_address

        self.webhook_address = webhook_address
        self.webhook_port = webhook_port
        # self.webhook_host = webhook_host
        # self.webhook_url = "http://{}:{}/webhooks".format(self.webhook_host, str(self.webhook_port))

        self.webhook_site = None  # type: Optional[web.TCPSite]
        self.runner = None  # type: Optional[web.AppRunner]
        self.app = None  # type: Optional[web.Application]

        self.is_stopped = True
        self.connection_id = connection_id

        self.in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self.loop = (
            None
        )  # type: Optional[asyncio.AbstractEventLoop]  # pragma: no cover
        logger.info("Initialised a webhook channel")

    async def connect(self):
        """
        Connect the webhook

        Connects the webhook via the webhook_address and webhook_port parameters
        """
        if self.is_stopped:
            self.app = web.Application()
            self.app.add_routes(
                [web.post("/webhooks/topic/{topic}/", self._receive_webhook)]
            )
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.webhook_site = web.TCPSite(
                self.runner, self.webhook_address, self.webhook_port
            )
            await self.webhook_site.start()
            self.is_stopped = False

    async def disconnect(self):
        """
        Disconnect.

        Shut-off and cleanup the webhook site, the runner and the web app, then stop the channel.
        """
        assert (
            self.webhook_site is not None
        ), "Application not connected, call connect first!"

        if not self.is_stopped:
            logger.info("Webhook app is shutdown.")
            await self.webhook_site.stop()
            await self.runner.shutdown()
            await self.runner.cleanup()
            await self.app.shutdown()
            await self.app.cleanup()
            self.is_stopped = True

    async def _receive_webhook(self, request: web.Request):
        """
        Receive a webhook request

        Get webhook request, turn it to envelop and send it to the agent to be picked up.
        """
        webhook_envelop = await self.to_envelope(self.connection_id, request)
        self.in_queue.put_nowait(webhook_envelop)  # type: ignore
        return web.Response(status=200)

    def send(self, request_envelope: Envelope) -> None:
        pass

    async def to_envelope(self, connection_id: PublicId, request: web.Request,) -> Envelope:
        """
        Convert a webhook request object into an Envelope containing an HttpMessage (from the 'http' Protocol).

        :param connection_id: the connection id
        :param request: the webhook request
        """

        payload_bytes = await request.read()

        context = EnvelopeContext(connection_id=connection_id)
        http_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            method=request.method,
            url=request.url,
            version=request.version,
            headers=json.dumps(dict(request.headers)),
            bodyy=payload_bytes if payload_bytes is not None else b"",
        )
        envelope = Envelope(
            to=self.agent_address,
            sender=request.remote,
            protocol_id=PublicId.from_str("fetchai/http:0.1.0"),
            context=context,
            message=HttpSerializer().encode(http_message),
        )
        return envelope


class WebhookConnection(Connection):
    """Proxy to the functionality of a webhook."""

    def __init__(
        self, webhook_address: str, webhook_port: int, **kwargs,
    ):
        """
        Initialize a connection.

        :param webhook_address: the webhook hostname / IP address
        :param webhook_port: the webhook port number
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http_client", "0.1.0")

        super().__init__(**kwargs)

        # self.webhook_host = webhook_host
        self.webhook_address = webhook_address
        self.webhook_port = webhook_port

        self.channel = WebhookChannel(
            agent_address=self.address,
            webhook_address=self.webhook_address,
            webhook_port=self.webhook_port,
            connection_id=self.connection_id,
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
            await self.channel.connect()

    async def disconnect(self) -> None:
        """
        Disconnect from a HTTP server.

        :return: None
        """
        if self.connection_status.is_connected:
            self.connection_status.is_connected = False
            await self.channel.disconnect()

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        pass

    async def receive(self, *args, **kwargs) -> Optional[Union["Envelope", None]]:
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

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
"""HTTP client connection and channel."""

import asyncio
import json
import logging
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from traceback import format_exc
from typing import Any, Optional, Set, Union, cast

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext

from packages.fetchai.protocols.http.message import HttpMessage

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500
PUBLIC_ID = PublicId.from_str("fetchai/http_client:0.5.0")

logger = logging.getLogger("aea.packages.fetchai.connections.http_client")

RequestId = str


class HTTPClientAsyncChannel:
    """A wrapper for a HTTPClient."""

    DEFAULT_TIMEOUT = 300  # default timeout in seconds
    DEFAULT_EXCEPTION_CODE = (
        600  # custom code to indicate there was exception during request
    )

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

        self._in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self._loop = (
            None
        )  # type: Optional[asyncio.AbstractEventLoop]  # pragma: no cover
        self.excluded_protocols = excluded_protocols
        self.is_stopped = True
        self._tasks: Set[Task] = set()

        self.logger = logger
        self.logger.info("Initialised the HTTP client channel")

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect channel using loop.

        :param loop: asyncio event loop to use

        :return: None
        """
        self._loop = loop
        self._in_queue = asyncio.Queue()
        self.is_stopped = False

    async def _http_request_task(self, request_http_message: HttpMessage) -> None:
        """
        Perform http request and send back response.

        :param request_http_message: HttpMessage with http request constructed.

        :return: None
        """
        if not self._loop:  # pragma: nocover
            raise ValueError("Channel is not connected")

        try:
            resp = await asyncio.wait_for(
                self._perform_http_request(request_http_message),
                timeout=self.DEFAULT_TIMEOUT,
            )
            envelope = self.to_envelope(
                self.connection_id,
                request_http_message,
                status_code=resp.status,
                headers=resp.headers,
                status_text=resp.reason,
                bodyy=resp._body  # pylint: disable=protected-access
                if resp._body is not None  # pylint: disable=protected-access
                else b"",
            )
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            envelope = self.to_envelope(
                self.connection_id,
                request_http_message,
                status_code=self.DEFAULT_EXCEPTION_CODE,
                headers={},
                status_text="HTTPConnection request error.",
                bodyy=format_exc().encode("utf-8"),
            )

        if self._in_queue is not None:
            await self._in_queue.put(envelope)

    async def _perform_http_request(
        self, request_http_message: HttpMessage
    ) -> ClientResponse:
        """
        Perform http request and return response.

        :param request_http_message: HttpMessage with http request constructed.

        :return: aiohttp.ClientResponse
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request_http_message.method,
                    url=request_http_message.url,
                    headers=request_http_message.headers,
                    data=request_http_message.bodyy,
                ) as resp:
                    await resp.read()
                return resp
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(
                f"Exception raised during http call: {request_http_message.method} {request_http_message.url}"
            )
            raise

    def send(self, request_envelope: Envelope) -> None:
        """
        Send an envelope with http request data to request.

        Convert an http envelope into an http request.
        Send the http request
        Wait for and receive its response
        Translate the response into a response envelop.
        Send the response envelope to the in-queue.

        :param request_envelope: the envelope containing an http request

        :return: None
        """
        if self._loop is None or self.is_stopped:
            raise ValueError("Can not send a message! Channel is not started!")

        if request_envelope is None:
            return

        if request_envelope.protocol_id in (self.excluded_protocols or []):
            self.logger.error(
                "This envelope cannot be sent with the http client connection: protocol_id={}".format(
                    request_envelope.protocol_id
                )
            )
            raise ValueError("Cannot send message.")

        assert isinstance(
            request_envelope.message, HttpMessage
        ), "Message not of type HttpMessage"

        request_http_message = cast(HttpMessage, request_envelope.message)

        if (
            request_http_message.performative != HttpMessage.Performative.REQUEST
        ):  # pragma: nocover
            self.logger.warning(
                "The HTTPMessage performative must be a REQUEST. Envelop dropped."
            )
            return

        task = self._loop.create_task(self._http_request_task(request_http_message))
        task.add_done_callback(self._task_done_callback)
        self._tasks.add(task)

    def _task_done_callback(self, task: Task) -> None:
        """
        Handle http request task completed.

        Removes tasks from _tasks.

        :param task: Task completed.

        :return: None
        """
        self._tasks.remove(task)
        self.logger.debug(f"Task completed: {task}")

    async def get_message(self) -> Union["Envelope", None]:
        """
        Get http response from in-queue.

        :return: None or envelope with http response.
        """
        if self._in_queue is None:
            raise ValueError("Looks like channel is not connected!")

        try:
            return await self._in_queue.get()
        except CancelledError:  # pragma: nocover
            return None

    def to_envelope(
        self,
        connection_id: PublicId,
        http_request_message: HttpMessage,
        status_code: int,
        headers: dict,
        status_text: Optional[Any],
        bodyy: bytes,
    ) -> Envelope:
        """
        Convert an HTTP response object (from the 'requests' library) into an Envelope containing an HttpMessage (from the 'http' Protocol).

        :param connection_id: the connection id
        :param http_request_message: the message of the http request envelop
        :param status_code: the http status code, int
        :param headers: dict of http response headers
        :param status_text: the http status_text, str
        :param bodyy: bytes of http response content

        :return: Envelope with http response data.
        """
        context = EnvelopeContext(connection_id=connection_id)
        http_message = HttpMessage(
            dialogue_reference=http_request_message.dialogue_reference,
            target=http_request_message.target,
            message_id=http_request_message.message_id,
            performative=HttpMessage.Performative.RESPONSE,
            status_code=status_code,
            headers=json.dumps(dict(headers.items())),
            status_text=status_text,
            bodyy=bodyy,
            version="",
        )
        envelope = Envelope(
            to=self.agent_address,
            sender="HTTP Server",
            protocol_id=PublicId.from_str("fetchai/http:0.3.0"),
            context=context,
            message=http_message,
        )
        return envelope

    async def _cancel_tasks(self) -> None:
        """Cancel all requests tasks pending."""
        for task in list(self._tasks):
            if task.done():  # pragma: nocover
                continue
            task.cancel()

        for task in list(self._tasks):
            try:
                await task
            except KeyboardInterrupt:  # pragma: nocover
                raise
            except BaseException:  # pragma: nocover # pylint: disable=broad-except
                pass  # nosec

    async def disconnect(self) -> None:
        """Disconnect."""
        if not self.is_stopped:
            self.logger.info("HTTP Client has shutdown on port: {}.".format(self.port))
            self.is_stopped = True

            await self._cancel_tasks()


class HTTPClientConnection(Connection):
    """Proxy to the functionality of the web client."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize a HTTP client connection."""
        super().__init__(**kwargs)
        host = cast(str, self.configuration.config.get("host"))
        port = cast(int, self.configuration.config.get("port"))
        assert host is not None and port is not None, "host and port must be set!"
        self.channel = HTTPClientAsyncChannel(
            self.address,
            host,
            port,
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
            self.channel.logger = self.logger
            await self.channel.connect(self._loop)

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
        try:
            return await self.channel.get_message()
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception("Exception on receive")
            return None

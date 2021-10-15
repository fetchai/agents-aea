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
import email
import logging
import ssl
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.tasks import Task
from traceback import format_exc
from typing import Any, Optional, Set, Tuple, cast

import aiohttp
import certifi  # pylint: disable=wrong-import-order
from aiohttp.client_reqrep import ClientResponse
from multidict import CIMultiDict, CIMultiDictProxy

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.http.dialogues import HttpDialogue as BaseHttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage


SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500
PUBLIC_ID = PublicId.from_str("fetchai/http_client:0.23.0")

_default_logger = logging.getLogger("aea.packages.fetchai.connections.http_client")

RequestId = str

ssl_context = ssl.create_default_context(cafile=certifi.where())


def headers_to_string(headers: CIMultiDictProxy) -> str:
    """
    Convert headers to string.

    :param headers: dict

    :return: str
    """
    msg = email.message.Message()
    for name, value in headers.items():
        msg.add_header(name, value)
    return msg.as_string()


HttpDialogue = BaseHttpDialogue


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self) -> None:
        """Initialize dialogues."""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The client connection maintains the dialogue on behalf of the server
            return HttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=str(HTTPClientConnection.connection_id),
            role_from_first_message=role_from_first_message,
            dialogue_class=HttpDialogue,
        )


class HTTPClientAsyncChannel:
    """A wrapper for a HTTPClient."""

    DEFAULT_TIMEOUT = 300  # default timeout in seconds
    DEFAULT_EXCEPTION_CODE = (
        600  # custom code to indicate there was exception during request
    )

    def __init__(
        self, agent_address: Address, address: str, port: int, connection_id: PublicId,
    ):
        """
        Initialize an http client channel.

        :param agent_address: the address of the agent.
        :param address: server hostname / IP address
        :param port: server port number
        :param connection_id: the id of the connection
        """
        self.agent_address = agent_address
        self.address = address
        self.port = port
        self.connection_id = connection_id
        self._dialogues = HttpDialogues()

        self._in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self._loop = (
            None
        )  # type: Optional[asyncio.AbstractEventLoop]  # pragma: no cover
        self.is_stopped = True
        self._tasks: Set[Task] = set()

        self.logger = _default_logger
        self.logger.debug("Initialised the HTTP client channel")

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect channel using loop.

        :param loop: asyncio event loop to use
        """
        self._loop = loop
        self._in_queue = asyncio.Queue()
        self.is_stopped = False

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[HttpMessage, Optional[HttpDialogue]]:
        """
        Get a message copy and dialogue related to this message.

        :param envelope: incoming envelope

        :return: Tuple[MEssage, Optional[Dialogue]]
        """
        message = cast(HttpMessage, envelope.message)
        dialogue = cast(Optional[HttpDialogue], self._dialogues.update(message))
        return message, dialogue

    async def _http_request_task(self, request_envelope: Envelope) -> None:
        """
        Perform http request and send back response.

        :param request_envelope: request envelope.
        """
        if not self._loop:  # pragma: nocover
            raise ValueError("Channel is not connected")

        request_http_message, dialogue = self._get_message_and_dialogue(
            request_envelope
        )

        if not dialogue:
            self.logger.warning(
                "Could not create dialogue for message={}".format(request_http_message)
            )
            return

        try:
            resp = await asyncio.wait_for(
                self._perform_http_request(request_http_message),
                timeout=self.DEFAULT_TIMEOUT,
            )
            envelope = self.to_envelope(
                request_http_message,
                status_code=resp.status,
                headers=resp.headers,
                status_text=resp.reason,
                body=resp._body  # pylint: disable=protected-access
                if resp._body is not None  # pylint: disable=protected-access
                else b"",
                dialogue=dialogue,
            )
        except Exception:  # pylint: disable=broad-except
            envelope = self.to_envelope(
                request_http_message,
                status_code=self.DEFAULT_EXCEPTION_CODE,
                headers=CIMultiDictProxy(CIMultiDict()),
                status_text="HTTPConnection request error.",
                body=format_exc().encode("utf-8"),
                dialogue=dialogue,
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
            if request_http_message.is_set("headers") and request_http_message.headers:
                headers: Optional[dict] = dict(
                    email.message_from_string(request_http_message.headers).items()
                )
            else:
                headers = None
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request_http_message.method,
                    url=request_http_message.url,
                    headers=headers,
                    data=request_http_message.body,
                    ssl=ssl_context,
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
        """
        if self._loop is None or self.is_stopped:
            raise ValueError("Can not send a message! Channel is not started!")

        if request_envelope is None:
            return

        enforce(
            isinstance(request_envelope.message, HttpMessage),
            "Message not of type HttpMessage",
        )

        request_http_message = cast(HttpMessage, request_envelope.message)

        if (
            request_http_message.performative != HttpMessage.Performative.REQUEST
        ):  # pragma: nocover
            self.logger.warning(
                "The HTTPMessage performative must be a REQUEST. Envelop dropped."
            )
            return

        task = self._loop.create_task(self._http_request_task(request_envelope))
        task.add_done_callback(self._task_done_callback)
        self._tasks.add(task)

    def _task_done_callback(self, task: Task) -> None:
        """
        Handle http request task completed.

        Removes tasks from _tasks.

        :param task: Task completed.
        """
        self._tasks.remove(task)
        self.logger.debug(f"Task completed: {task}")

    async def get_message(self) -> Optional["Envelope"]:
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

    @staticmethod
    def to_envelope(
        http_request_message: HttpMessage,
        status_code: int,
        headers: CIMultiDictProxy,
        status_text: Optional[Any],
        body: bytes,
        dialogue: HttpDialogue,
    ) -> Envelope:
        """
        Convert an HTTP response object (from the 'requests' library) into an Envelope containing an HttpMessage (from the 'http' Protocol).

        :param http_request_message: the message of the http request envelop
        :param status_code: the http status code, int
        :param headers: dict of http response headers
        :param status_text: the http status_text, str
        :param body: bytes of http response content
        :param dialogue: the http dialogue

        :return: Envelope with http response data.
        """
        http_message = dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_request_message,
            status_code=status_code,
            headers=headers_to_string(headers),
            status_text=status_text,
            body=body,
            version="",
        )
        envelope = Envelope(
            to=http_message.to, sender=http_message.sender, message=http_message,
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

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a HTTP client connection.

        :param kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        host = cast(str, self.configuration.config.get("host"))
        port = cast(int, self.configuration.config.get("port"))
        if host is None or port is None:  # pragma: nocover
            raise ValueError("host and port must be set!")
        self.channel = HTTPClientAsyncChannel(
            self.address, host, port, connection_id=self.connection_id,
        )

    async def connect(self) -> None:
        """Connect to a HTTP server."""
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            self.channel.logger = self.logger
            await self.channel.connect(self.loop)

    async def disconnect(self) -> None:
        """Disconnect from a HTTP server."""
        if self.is_disconnected:
            return  # pragma: nocover
        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        """
        self._ensure_connected()
        self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the envelope received, or None.
        """
        self._ensure_connected()
        try:
            return await self.channel.get_message()
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception("Exception on receive")
            return None

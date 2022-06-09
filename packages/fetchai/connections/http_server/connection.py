# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""HTTP server connection, channel, server, and handler."""
import asyncio
import email
import logging
import ssl
from abc import ABC, abstractmethod
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from concurrent.futures._base import CancelledError as FuturesCancelledError
from traceback import format_exc
from typing import Any, Dict, Optional, cast
from urllib.parse import parse_qs, urlparse

from aiohttp import web
from aiohttp.web_request import BaseRequest
from openapi_core import create_spec
from openapi_core.validation.request.datatypes import OpenAPIRequest, RequestParameters
from openapi_core.validation.request.shortcuts import validate_request
from openapi_core.validation.request.validators import RequestValidator
from openapi_spec_validator.exceptions import (  # pylint: disable=wrong-import-order
    OpenAPIValidationError,
)
from openapi_spec_validator.schemas import (  # pylint: disable=wrong-import-order
    read_yaml_file,
)
from werkzeug.datastructures import (  # pylint: disable=wrong-import-order
    ImmutableMultiDict,
)

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.http.dialogues import HttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage


SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500

_default_logger = logging.getLogger("aea.packages.fetchai.connections.http_server")

RequestId = DialogueLabel
PUBLIC_ID = PublicId.from_str("fetchai/http_server:0.22.0")


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param self_address: address of the dialogues maintainer.
        :param kwargs: keyword arguments.
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
            return HttpDialogue.Role.CLIENT

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


def headers_to_string(headers: Dict) -> str:
    """
    Convert headers to string.

    :param headers: dict

    :return: str
    """
    msg = email.message.Message()
    for name, value in headers.items():
        msg.add_header(name, value)
    return msg.as_string()


class Request(OpenAPIRequest):
    """Generic request object."""

    @property
    def is_id_set(self) -> bool:
        """Check if id is set."""
        return self._id is not None

    @property
    def id(self) -> RequestId:
        """Get the request id."""
        return self._id

    @id.setter
    def id(self, request_id: RequestId) -> None:
        """Set the request id."""
        self._id = request_id

    @classmethod
    async def create(cls, http_request: BaseRequest) -> "Request":
        """
        Create a request.

        :param http_request: http_request
        :return: a request
        """
        method = http_request.method.lower()

        parsed_path = urlparse(http_request.path_qs)

        url = http_request.url

        body = await http_request.read()

        mimetype = http_request.content_type

        query_params = parse_qs(parsed_path.query, keep_blank_values=True)

        parameters = RequestParameters(
            query=ImmutableMultiDict(query_params),  # type: ignore
            header=headers_to_string(dict(http_request.headers)),
            path={},
        )

        request = Request(
            full_url_pattern=str(url),
            method=method,
            parameters=parameters,
            body=body,
            mimetype=mimetype,
        )
        return request

    def to_envelope_and_set_id(
        self,
        dialogues: HttpDialogues,
        target_skill_id: PublicId,
    ) -> Envelope:
        """
        Process incoming API request by packaging into Envelope and sending it in-queue.

        :param dialogues: the http dialogues
        :param target_skill_id: the target skill id

        :return: envelope
        """
        url = self.full_url_pattern
        http_message, http_dialogue = dialogues.create(
            counterparty=str(target_skill_id),
            performative=HttpMessage.Performative.REQUEST,
            method=self.method,
            url=url,
            headers=self.parameters.header,
            body=self.body if self.body is not None else b"",
            version="",
        )
        dialogue = cast(HttpDialogue, http_dialogue)
        self.id = dialogue.incomplete_dialogue_label
        envelope = Envelope(
            to=http_message.to,
            sender=http_message.sender,
            message=http_message,
        )
        return envelope


class Response(web.Response):
    """Generic response object."""

    @classmethod
    def from_message(cls, http_message: HttpMessage) -> "Response":
        """
        Turn an envelope into a response.

        :param http_message: the http_message
        :return: the response
        """
        if http_message.performative == HttpMessage.Performative.RESPONSE:

            if http_message.is_set("headers") and http_message.headers:
                headers: Optional[dict] = dict(
                    email.message_from_string(http_message.headers).items()
                )
            else:
                headers = None

            # if content length header provided, it should correspond to actuyal body length
            if headers and "Content-Length" in headers:
                headers["Content-Length"] = str(len(http_message.body or ""))

            response = cls(
                status=http_message.status_code,
                reason=http_message.status_text,
                body=http_message.body,
                headers=headers,
            )
        else:  # pragma: nocover
            response = cls(status=SERVER_ERROR, text="Server error")
        return response


class APISpec:
    """API Spec class to verify a request against an OpenAPI/Swagger spec."""

    def __init__(
        self,
        api_spec_path: Optional[str] = None,
        server: Optional[str] = None,
        logger: logging.Logger = _default_logger,
    ):
        """
        Initialize the API spec.

        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        :param server: the server url
        :param logger: the logger
        """
        self._validator = None  # type: Optional[RequestValidator]
        self.logger = logger
        if api_spec_path is not None:
            try:
                api_spec_dict = read_yaml_file(api_spec_path)
                if server is not None:
                    api_spec_dict["servers"] = [{"url": server}]
                api_spec = create_spec(api_spec_dict)
                self._validator = RequestValidator(api_spec)
            except OpenAPIValidationError as e:  # pragma: nocover
                self.logger.error(
                    f"API specification YAML source file not correctly formatted: {str(e)}"
                )
            except Exception:
                self.logger.exception(
                    "API specification YAML source file not correctly formatted."
                )
                raise

    def verify(self, request: Request) -> bool:
        """
        Verify a http_method, url and param against the provided API spec.

        :param request: the request object
        :return: whether or not the request conforms with the API spec
        """
        if self._validator is None:
            self.logger.debug("Skipping API verification!")
            return True

        try:
            validate_request(self._validator, request)
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception("APISpec verify error")
            return False
        return True


class BaseAsyncChannel(ABC):
    """Base asynchronous channel class."""

    def __init__(self, address: Address, connection_id: PublicId) -> None:
        """
        Initialize a channel.

        :param address: the address of the agent.
        :param connection_id: public id of connection using this channel.
        """
        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self.is_stopped = True
        self.address = address
        self.connection_id = connection_id

    @abstractmethod
    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect.

        Upon HTTP Channel connection, start the HTTP Server in its own thread.

        :param loop: asyncio event loop
        """
        self._loop = loop
        self._in_queue = asyncio.Queue()
        self.is_stopped = False

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

    @abstractmethod
    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope in_queue.

        :param envelope: the envelope
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server.
        """


class HTTPChannel(BaseAsyncChannel):
    """A wrapper for an RESTful API with an internal HTTPServer."""

    RESPONSE_TIMEOUT = 5.0

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        target_skill_id: PublicId,
        api_spec_path: Optional[str],
        connection_id: PublicId,
        timeout_window: float = RESPONSE_TIMEOUT,
        logger: logging.Logger = _default_logger,
        ssl_cert_path: Optional[str] = None,
        ssl_key_path: Optional[str] = None,
    ):
        """
        Initialize a channel and process the initial API specification from the file path (if given).

        :param address: the address of the agent.
        :param host: RESTful API hostname / IP address
        :param port: RESTful API port number
        :param target_skill_id: the skill id which handles the requests
        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        :param connection_id: public id of connection using this channel.
        :param timeout_window: the timeout (in seconds) for a request to be handled.
        :param logger: the logger
        :param ssl_cert_path:  optional path to ssl certificate
        :param ssl_key_path: optional path to ssl key
        """
        super().__init__(address=address, connection_id=connection_id)
        self.host = host
        self.port = port
        self.ssl_cert_path = ssl_cert_path
        self.ssl_key_path = ssl_key_path
        self.target_skill_id = target_skill_id
        if self.ssl_cert_path and self.ssl_key_path:
            self.server_address = "https://{}:{}".format(self.host, self.port)
        else:
            self.server_address = "http://{}:{}".format(self.host, self.port)

        self._api_spec = APISpec(api_spec_path, self.server_address, logger)
        self.timeout_window = timeout_window
        self.http_server: Optional[web.TCPSite] = None
        self.pending_requests: Dict[RequestId, Future] = {}
        self._dialogues = HttpDialogues(str(HTTPServerConnection.connection_id))
        self.logger = logger

    @property
    def api_spec(self) -> APISpec:
        """Get the api spec."""
        return self._api_spec

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect.

        Upon HTTP Channel connection, start the HTTP Server in its own thread.

        :param loop: asyncio event loop
        """
        if self.is_stopped:
            await super().connect(loop)

            try:
                await self._start_http_server()
                self.logger.info(
                    "HTTP Server has connected to port: {}.".format(self.port)
                )
            except Exception:  # pragma: nocover # pylint: disable=broad-except
                self.is_stopped = True
                self._in_queue = None
                self.logger.exception(
                    "Failed to start server on {}:{}.".format(self.host, self.port)
                )

    async def _http_handler(self, http_request: BaseRequest) -> Response:
        """
        Verify the request then send the request to Agent as an envelope.

        :param http_request: the request object

        :return: a tuple of response code and response description
        """
        request = await Request.create(http_request)
        if self._in_queue is None:  # pragma: nocover
            raise ValueError("Channel not connected!")

        is_valid_request = self.api_spec.verify(request)

        if not is_valid_request:
            self.logger.warning(f"request is not valid: {request}")
            return Response(status=NOT_FOUND, reason="Request Not Found")

        try:
            # turn request into envelope
            envelope = request.to_envelope_and_set_id(
                self._dialogues, self.target_skill_id
            )

            self.pending_requests[request.id] = Future()

            # send the envelope to the agent's inbox (via self.in_queue)
            await self._in_queue.put(envelope)
            # wait for response envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes

            response_message = await asyncio.wait_for(
                self.pending_requests[request.id],
                timeout=self.timeout_window,
            )
            return Response.from_message(response_message)

        except asyncio.TimeoutError:
            self.logger.warning(
                f"Request timed out! Request={request} not handled as a result. Ensure requests (protocol_id={HttpMessage.protocol_id}) are handled by a skill!"
            )
            return Response(status=REQUEST_TIMEOUT, reason="Request Timeout")
        except FuturesCancelledError:
            return Response(  # pragma: nocover
                status=SERVER_ERROR, reason="Server terminated unexpectedly."
            )
        except BaseException:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception("Error during handling incoming request")
            return Response(
                status=SERVER_ERROR, reason="Server Error", text=format_exc()
            )
        finally:
            if request.is_id_set:
                self.pending_requests.pop(request.id, None)

    async def _start_http_server(self) -> None:
        """Start http server."""
        server = web.Server(self._http_handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        ssl_context = None
        if self.ssl_cert_path and self.ssl_key_path:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_cert_path, self.ssl_key_path)
        self.http_server = web.TCPSite(
            runner, self.host, self.port, ssl_context=ssl_context
        )
        await self.http_server.start()

    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope in_queue.

        :param envelope: the envelope
        """
        if self.http_server is None:  # pragma: nocover
            raise ValueError("Server not connected, call connect first!")

        message = cast(HttpMessage, envelope.message)
        dialogue = self._dialogues.update(message)

        if dialogue is None:
            self.logger.warning(
                "Could not create dialogue for message={}".format(message)
            )
            return

        future = self.pending_requests.pop(dialogue.incomplete_dialogue_label, None)

        if not future:
            self.logger.warning(
                "Dropping message={} for incomplete_dialogue_label={} which has timed out.".format(
                    message, dialogue.incomplete_dialogue_label
                )
            )
            return
        if not future.done():
            future.set_result(message)

    async def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server.
        """
        if self.http_server is None:  # pragma: nocover
            raise ValueError("Server not connected, call connect first!")

        if not self.is_stopped:
            await self.http_server.stop()
            self.logger.info("HTTP Server has shutdown on port: {}.".format(self.port))
            self.is_stopped = True
            self._in_queue = None


class HTTPServerConnection(Connection):
    """Proxy to the functionality of the http server implementing a RESTful API specification."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a HTTP server connection."""
        super().__init__(**kwargs)
        host = cast(Optional[str], self.configuration.config.get("host"))
        port = cast(Optional[int], self.configuration.config.get("port"))
        target_skill_id_ = cast(
            Optional[str], self.configuration.config.get("target_skill_id")
        )
        if host is None or port is None or target_skill_id_ is None:  # pragma: nocover
            raise ValueError("host and port and target_skill_id must be set!")
        target_skill_id = PublicId.try_from_str(target_skill_id_)
        if target_skill_id is None:  # pragma: nocover
            raise ValueError("Provided target_skill_id is not a valid public id.")
        api_spec_path = cast(
            Optional[str], self.configuration.config.get("api_spec_path")
        )
        ssl_cert_path = cast(Optional[str], self.configuration.config.get("ssl_cert"))
        ssl_key_path = cast(Optional[str], self.configuration.config.get("ssl_key"))

        if bool(ssl_cert_path) != bool(ssl_key_path):  # pragma: nocover
            raise ValueError("Please specify both ssl_cert and ssl_key or neither.")

        self.channel = HTTPChannel(
            self.address,
            host,
            port,
            target_skill_id,
            api_spec_path,
            connection_id=self.connection_id,
            logger=self.logger,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
        )

    async def connect(self) -> None:
        """Connect to the http channel."""
        if self.is_connected:
            return

        self.state = ConnectionStates.connecting
        self.channel.logger = self.logger
        await self.channel.connect(loop=self.loop)
        if self.channel.is_stopped:
            self.state = ConnectionStates.disconnected
        else:
            self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """Disconnect from HTTP channel."""
        if self.is_disconnected:
            return

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
        except CancelledError:  # pragma: no cover
            return None

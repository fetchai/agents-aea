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
"""HTTP server connection, channel, server, and handler."""
import asyncio
import email
import logging
from abc import ABC, abstractmethod
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from concurrent.futures._base import CancelledError as FuturesCancelledError
from traceback import format_exc
from typing import Dict, Optional, Set, cast
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
from aea.mail.base import Envelope, EnvelopeContext, Message, URI
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
PUBLIC_ID = PublicId.from_str("fetchai/http_server:0.14.0")


class HttpDialogues(BaseHttpDialogues):
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
            return HttpDialogue.Role.CLIENT

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


def headers_to_string(headers: Dict):
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
    def is_id_set(self):
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
            query=ImmutableMultiDict(query_params),
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
        self, connection_id: PublicId, agent_address: str, dialogues: HttpDialogues,
    ) -> Envelope:
        """
        Process incoming API request by packaging into Envelope and sending it in-queue.

        :param connection_id: id of the connection
        :param agent_address: agent's address
        :param dialogue_reference: new dialog refernece for envelope

        :return: envelope
        """
        url = self.full_url_pattern
        uri = URI(self.full_url_pattern)
        context = EnvelopeContext(connection_id=connection_id, uri=uri)
        http_message, http_dialogue = dialogues.create(
            counterparty=agent_address,
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
            protocol_id=http_message.protocol_id,
            context=context,
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

    def __init__(self, address: Address, connection_id: PublicId,) -> None:
        """
        Initialize a channel.

        :param address: the address of the agent.
        :param connection_id: public id of connection using this chanel.
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

        Upon HTTP Channel connection, kickstart the HTTP Server in its own thread.

        :param loop: asyncio event loop

        :return: None
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
        :return: None
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server.
        """


class HTTPChannel(BaseAsyncChannel):
    """A wrapper for an RESTful API with an internal HTTPServer."""

    RESPONSE_TIMEOUT = 300

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        api_spec_path: Optional[str],
        connection_id: PublicId,
        restricted_to_protocols: Set[PublicId],
        timeout_window: float = 5.0,
        logger: logging.Logger = _default_logger,
    ):
        """
        Initialize a channel and process the initial API specification from the file path (if given).

        :param address: the address of the agent.
        :param host: RESTful API hostname / IP address
        :param port: RESTful API port number
        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        :param connection_id: public id of connection using this chanel.
        :param restricted_to_protocols: set of restricted protocols
        :param timeout_window: the timeout (in seconds) for a request to be handled.
        """
        super().__init__(address=address, connection_id=connection_id)
        self.host = host
        self.port = port
        self.server_address = "http://{}:{}".format(self.host, self.port)
        self.restricted_to_protocols = restricted_to_protocols

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

        Upon HTTP Channel connection, kickstart the HTTP Server in its own thread.

        :param loop: asyncio event loop

        :return: None
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

        :param request: the request object

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
                self.connection_id, self.address, dialogues=self._dialogues,
            )

            self.pending_requests[request.id] = Future()

            # send the envelope to the agent's inbox (via self.in_queue)
            await self._in_queue.put(envelope)
            # wait for response envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes

            response_message = await asyncio.wait_for(
                self.pending_requests[request.id], timeout=self.RESPONSE_TIMEOUT,
            )

            return Response.from_message(response_message)

        except asyncio.TimeoutError:
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
        self.http_server = web.TCPSite(runner, self.host, self.port)
        await self.http_server.start()

    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope in_queue.

        :param envelope: the envelope
        :return: None
        """
        if self.http_server is None:  # pragma: nocover
            raise ValueError("Server not connected, call connect first!")

        if envelope.protocol_id not in self.restricted_to_protocols:
            self.logger.error(
                "This envelope cannot be sent with the http connection: protocol_id={}".format(
                    envelope.protocol_id
                )
            )
            raise ValueError("Cannot send message.")

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

    def __init__(self, **kwargs):
        """Initialize a HTTP server connection."""
        super().__init__(**kwargs)
        host = cast(str, self.configuration.config.get("host"))
        port = cast(int, self.configuration.config.get("port"))
        if host is None or port is None:  # pragma: nocover
            raise ValueError("host and port must be set!")
        api_spec_path = cast(
            Optional[str], self.configuration.config.get("api_spec_path")
        )
        self.channel = HTTPChannel(
            self.address,
            host,
            port,
            api_spec_path,
            connection_id=self.connection_id,
            restricted_to_protocols=self.restricted_to_protocols,
            logger=self.logger,
        )

    async def connect(self) -> None:
        """
        Connect to the http.

        :return: None
        """
        if self.is_connected:
            return

        self._state.set(ConnectionStates.connecting)
        self.channel.logger = self.logger
        await self.channel.connect(loop=self.loop)
        if self.channel.is_stopped:
            self._state.set(ConnectionStates.disconnected)
        else:
            self._state.set(ConnectionStates.connected)

    async def disconnect(self) -> None:
        """
        Disconnect from HTTP.

        :return: None
        """
        if self.is_disconnected:
            return

        self._state.set(ConnectionStates.disconnecting)
        await self.channel.disconnect()
        self._state.set(ConnectionStates.disconnected)

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        self._ensure_connected()
        self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :return: the envelope received, or None.
        """
        self._ensure_connected()
        try:
            return await self.channel.get_message()
        except CancelledError:  # pragma: no cover
            return None

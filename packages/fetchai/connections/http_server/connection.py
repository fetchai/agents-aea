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
from traceback import format_exc
from typing import Dict, Optional, Set, cast
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

from aiohttp import web
from aiohttp.web_request import BaseRequest

from openapi_core import create_spec
from openapi_core.validation.request.datatypes import (
    OpenAPIRequest,
    RequestParameters,
)
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

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI

from packages.fetchai.protocols.http.message import HttpMessage

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500

logger = logging.getLogger("aea.packages.fetchai.connections.http_server")

RequestId = str
PUBLIC_ID = PublicId.from_str("fetchai/http_server:0.5.0")


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

        request.id = uuid4().hex
        return request

    def to_envelope(self, connection_id: PublicId, agent_address: str) -> Envelope:
        """
        Process incoming API request by packaging into Envelope and sending it in-queue.

        The Envelope's message body contains the "performative", "path", "params", and "payload".

        :param http_method: the http method
        :param url: the url
        :param param: the parameter
        :param body: the body
        """
        url = (
            self.full_url_pattern
            if self.parameters.query == {}
            else self.full_url_pattern + "?" + urlencode(self.parameters.query)
        )
        uri = URI(self.full_url_pattern)
        context = EnvelopeContext(connection_id=connection_id, uri=uri)
        http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method=self.method,
            url=url,
            headers=self.parameters.header,
            bodyy=self.body if self.body is not None else b"",
            version="",
        )
        envelope = Envelope(
            to=agent_address,
            sender=self.id,
            protocol_id=PublicId.from_str("fetchai/http:0.3.0"),
            context=context,
            message=http_message,
        )
        return envelope


class Response(web.Response):
    """Generic response object."""

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> "Response":
        """
        Turn an envelope into a response.

        :param envelope: the envelope
        :return: the response
        """
        assert isinstance(
            envelope.message, HttpMessage
        ), "Message not of type HttpMessage"

        http_message = cast(HttpMessage, envelope.message)
        if http_message.performative == HttpMessage.Performative.RESPONSE:
            response = cls(
                status=http_message.status_code,
                reason=http_message.status_text,
                body=http_message.bodyy,
            )
        else:
            response = cls(status=SERVER_ERROR, text="Server error")
        return response


class APISpec:
    """API Spec class to verify a request against an OpenAPI/Swagger spec."""

    def __init__(
        self, api_spec_path: Optional[str] = None, server: Optional[str] = None
    ):
        """
        Initialize the API spec.

        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """
        self._validator = None  # type: Optional[RequestValidator]
        if api_spec_path is not None:
            try:
                api_spec_dict = read_yaml_file(api_spec_path)
                if server is not None:
                    api_spec_dict["servers"] = [{"url": server}]
                api_spec = create_spec(api_spec_dict)
                self._validator = RequestValidator(api_spec)
            except OpenAPIValidationError as e:  # pragma: nocover
                logger.error(
                    f"API specification YAML source file not correctly formatted: {str(e)}"
                )
            except Exception:
                logger.exception(
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
            logger.debug("Skipping API verification!")
            return True

        try:
            validate_request(self._validator, request)
        except Exception:  # pragma: nocover # pylint: disable=broad-except
            logger.exception("APISpec verify error")
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

        self._api_spec = APISpec(api_spec_path, self.server_address)
        self.timeout_window = timeout_window
        self.http_server: Optional[web.TCPSite] = None
        self.pending_requests: Dict[RequestId, Future] = {}

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
        assert self._in_queue is not None, "Channel not connected!"

        is_valid_request = self.api_spec.verify(request)

        if not is_valid_request:
            self.logger.warning(f"request is not valid: {request}")
            return Response(status=NOT_FOUND, reason="Request Not Found")

        try:
            self.pending_requests[request.id] = Future()
            # turn request into envelope
            envelope = request.to_envelope(self.connection_id, self.address)
            # send the envelope to the agent's inbox (via self.in_queue)
            await self._in_queue.put(envelope)
            # wait for response envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes

            response_envelope = await asyncio.wait_for(
                self.pending_requests[request.id], timeout=self.RESPONSE_TIMEOUT
            )
            return Response.from_envelope(response_envelope)

        except asyncio.TimeoutError:
            return Response(status=REQUEST_TIMEOUT, reason="Request Timeout")
        except BaseException:  # pragma: nocover # pylint: disable=broad-except
            return Response(
                status=SERVER_ERROR, reason="Server Error", text=format_exc()
            )
        finally:
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
        assert self.http_server is not None, "Server not connected, call connect first!"

        if envelope.protocol_id not in self.restricted_to_protocols:
            self.logger.error(
                "This envelope cannot be sent with the http connection: protocol_id={}".format(
                    envelope.protocol_id
                )
            )
            raise ValueError("Cannot send message.")

        future = self.pending_requests.pop(envelope.to, None)

        if not future:
            self.logger.warning(
                "Dropping envelope for request id {} which has timed out.".format(
                    envelope.to
                )
            )
        else:
            future.set_result(envelope)

    async def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server.
        """
        assert self.http_server is not None, "Server not connected, call connect first!"

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
        assert host is not None and port is not None, "host and port must be set!"
        api_spec_path = cast(str, self.configuration.config.get("api_spec_path"))
        self.channel = HTTPChannel(
            self.address,
            host,
            port,
            api_spec_path,
            connection_id=self.connection_id,
            restricted_to_protocols=self.restricted_to_protocols,
        )

    async def connect(self) -> None:
        """
        Connect to the http.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.channel.logger = self.logger
            await self.channel.connect(loop=self.loop)
            self.connection_status.is_connected = not self.channel.is_stopped

    async def disconnect(self) -> None:
        """
        Disconnect from HTTP.

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

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
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
        except CancelledError:  # pragma: no cover
            return None

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

"""HTTP server connection, channel, server, and handler"""

import asyncio
import logging
from asyncio import CancelledError
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from typing import Dict, Optional, Set, cast
from uuid import uuid4

from openapi_core import create_spec
from openapi_core.validation.request.datatypes import (
    OpenAPIRequest,
    RequestParameters,
)
from openapi_core.validation.request.shortcuts import validate_request
from openapi_core.validation.request.validators import RequestValidator

from openapi_spec_validator.schemas import read_yaml_file

from werkzeug.datastructures import ImmutableMultiDict

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500

logger = logging.getLogger("aea.packages.fetchai.connections.http_server")

RequestId = str


class Request(OpenAPIRequest):
    """Generic request object."""

    @property
    def id(self) -> RequestId:
        return self._id

    @id.setter
    def id(self, id: RequestId) -> None:
        self._id = id

    @classmethod
    def create(cls, request_handler: BaseHTTPRequestHandler) -> "Request":
        method = request_handler.command.lower()

        # gets deduced by path finder against spec
        path = {}  # type: Dict

        url = "http://{}:{}{}".format(
            *request_handler.server.server_address, request_handler.path
        )

        content_length = request_handler.headers["Content-Length"]
        body = (
            None
            if content_length is None
            else request_handler.rfile.read(int(content_length)).decode()
        )

        mimetype = request_handler.headers.get_content_type()
        parameters = RequestParameters(
            query=ImmutableMultiDict(request_handler.headers.get_params()),
            header=request_handler.headers,
            path=path,
        )
        request = Request(
            full_url_pattern=url,
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
        uri = URI(self.full_url_pattern)
        context = EnvelopeContext(connection_id=connection_id, uri=uri)
        http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method=self.method,
            url=self.full_url_pattern,
            headers=self.parameters.header.as_string(),
            bodyy=self.body.encode() if self.body is not None else b"",
            version="",
        )
        envelope = Envelope(
            to=agent_address,
            sender=self.id,
            protocol_id=PublicId.from_str("fetchai/http:0.1.0"),
            context=context,
            message=HttpSerializer().encode(http_message),
        )
        return envelope


class Response:
    """Generic response object."""

    def __init__(
        self, status_code: int, status_text: str, body: Optional[bytes] = None
    ):
        """
        Initialize the response.

        :param status_code: the status code
        :param status_text: the status text
        :param body: the body
        """
        self._status_code = status_code
        self._status_text = status_text
        self._body = body

    @property
    def status_code(self) -> int:
        """Get the status code."""
        return self._status_code

    @property
    def status_text(self) -> str:
        """Get the status text."""
        return self._status_text

    @property
    def body(self) -> Optional[bytes]:
        """Get the body."""
        return self._body

    @classmethod
    def from_envelope(cls, envelope: Optional[Envelope] = None) -> "Response":
        """
        Turn an envelope into a response.

        :param envelope: the envelope
        :return: the response
        """
        if envelope is not None:
            http_message = cast(HttpMessage, HttpSerializer().decode(envelope.message))
            if http_message.performative == HttpMessage.Performative.RESPONSE:
                response = Response(
                    http_message.status_code,
                    http_message.status_text,
                    http_message.bodyy,
                )
            else:
                response = Response(SERVER_ERROR, "Server error")
        else:
            response = Response(REQUEST_TIMEOUT, "Request Timeout")
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
            except Exception:
                logger.error(
                    "API specification YAML source file not correctly formatted."
                )

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
        except Exception:
            return False
        return True


class HTTPChannel:
    """A wrapper for an RESTful API with an internal HTTPServer."""

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
        :param timeout_window: the timeout (in seconds) for a request to be handled.
        """
        self.address = address
        self.host = host
        self.port = port
        self.server_address = "http://{}:{}".format(self.host, self.port)
        self.connection_id = connection_id
        self.restricted_to_protocols = restricted_to_protocols
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self.thread = None  # type: Optional[Thread]
        self.lock = Lock()
        self.is_stopped = True
        self._api_spec = APISpec(api_spec_path, self.server_address)
        self.timeout_window = timeout_window
        self.http_server = None  # type: Optional[HTTPServer]
        self.dispatch_ready_envelopes = {}  # type: Dict[RequestId, Envelope]
        self.timed_out_request_ids = set()  # type: Set[RequestId]
        self.pending_request_ids = set()  # type: Set[RequestId]

    @property
    def api_spec(self) -> APISpec:
        """Get the api spec."""
        return self._api_spec

    def connect(self):
        """
        Connect.

        Upon HTTP Channel connection, kickstart the HTTP Server in its own thread.
        """
        if self.is_stopped:
            try:
                self.http_server = HTTPServer(
                    (self.host, self.port), HTTPHandlerFactory(self)
                )
                logger.info("HTTP Server has connected to port: {}.".format(self.port))
                self.thread = Thread(target=self.http_server.serve_forever)
                self.thread.start()
                self.is_stopped = False
            except OSError:
                logger.error(
                    "{}:{} is already in use, please try another Socket.".format(
                        self.host, self.port
                    )
                )

    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope in_queue.

        :param envelope: the envelope
        :return: None
        """
        assert self.http_server is not None, "Server not connected, call connect first!"

        if envelope.protocol_id not in self.restricted_to_protocols:
            logger.error(
                "This envelope cannot be sent with the http connection: protocol_id={}".format(
                    envelope.protocol_id
                )
            )
            raise ValueError("Cannot send message.")

        if envelope.to in self.timed_out_request_ids:
            self.timed_out_request_ids.remove(envelope.to)
            logger.warning(
                "Dropping envelope for request id {} which has timed out.".format(
                    envelope.to
                )
            )
        elif envelope.to in self.pending_request_ids:
            self.pending_request_ids.remove(envelope.to)
            self.dispatch_ready_envelopes.update({envelope.to: envelope})
        else:
            logger.warning(
                "Dropping envelope for unknown request id {}.".format(envelope.to)
            )

    def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server and join the thread, then stop the channel.
        """
        assert (
            self.http_server is not None and self.thread is not None
        ), "Server not connected, call connect first!"

        if not self.is_stopped:
            self.http_server.shutdown()
            logger.info("HTTP Server has shutdown on port: {}.".format(self.port))
            self.is_stopped = True
            self.thread.join()

    async def process(self, request: Request) -> Response:
        """
        Verify the request then send the request to Agent as an envelope.

        :param request: the request object
        :return: a tuple of response code and response description
        """
        assert self.in_queue is not None, "Channel not connected!"

        is_valid_request = self.api_spec.verify(request)

        if is_valid_request:
            self.pending_request_ids.add(request.id)
            # turn request into envelope
            envelope = request.to_envelope(self.connection_id, self.address)
            # send the envelope to the agent's inbox (via self.in_queue)
            self.in_queue.put_nowait(envelope)
            # wait for response envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes
            response_envelope = await self.get_response(envelope.sender)
            # turn response envelope into response
            response = Response.from_envelope(response_envelope)
        else:
            response = Response(NOT_FOUND, "Request Not Found")

        return response

    async def get_response(
        self, request_id: RequestId, sleep: float = 0.1
    ) -> Optional[Envelope]:
        """
        Get the response.

        :param request_id: the request id
        :return: the envelope
        """
        not_received = True
        timeout_count = 0.0
        while not_received and timeout_count <= self.timeout_window:
            envelope = self.dispatch_ready_envelopes.get(request_id, None)
            if envelope is None:
                await asyncio.sleep(sleep)
                timeout_count += sleep
            else:
                not_received = False
        if not_received:
            self.timed_out_request_ids.add(request_id)
        return envelope


def HTTPHandlerFactory(channel: HTTPChannel):
    class HTTPHandler(BaseHTTPRequestHandler):
        """HTTP Handler class to deal with incoming requests."""

        def __init__(self, *args, **kwargs):
            """Initialize a HTTP Handler."""
            self._channel = channel
            super(HTTPHandler, self).__init__(*args, **kwargs)

        @property
        def channel(self) -> HTTPChannel:
            """Get the http channel."""
            return self._channel

        def do_HEAD(self):
            """Deal with header only requests."""
            self.send_response(SUCCESS)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            request = Request.create(self)

            future = asyncio.run_coroutine_threadsafe(
                self.channel.process(request), self.channel.loop
            )
            response = future.result()

            self.send_response(response.status_code, response.status_text)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if response.body is not None:
                self.wfile.write(response.body)

        def do_POST(self):
            """Respond to a POST request."""
            request = Request.create(self)

            future = asyncio.run_coroutine_threadsafe(
                self.channel.process(request), self.channel.loop
            )
            response = future.result()

            self.send_response(response.status_code, response.status_text)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if response.body is not None:
                self.wfile.write(response.body)

    return HTTPHandler


class HTTPServerConnection(Connection):
    """Proxy to the functionality of the http server implementing a RESTful API specification."""

    def __init__(
        self, host: str, port: int, api_spec_path: Optional[str] = None, **kwargs,
    ):
        """
        Initialize a connection to an RESTful API.

        :param address: the address of the agent.
        :param host: RESTful API hostname / IP address
        :param port: RESTful API port number
        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """
        super().__init__(**kwargs)
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
            self.connection_status.is_connected = True
            self.channel.in_queue = asyncio.Queue()
            self.channel.loop = self.loop
            self.channel.connect()

    async def disconnect(self) -> None:
        """
        Disconnect from HTTP.

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
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from the connection configuration.

        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        host = cast(str, configuration.config.get("host"))
        port = cast(int, configuration.config.get("port"))
        api_spec_path = cast(str, configuration.config.get("api_spec_path"))
        return HTTPServerConnection(
            host, port, api_spec_path, address=address, configuration=configuration
        )

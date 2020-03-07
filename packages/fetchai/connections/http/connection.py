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

"""HTTP connection, channel, server, and handler"""

import asyncio
import json
import logging
from asyncio import CancelledError
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from typing import Dict, Optional, Set, cast
from uuid import uuid4

from flex.core import load, validate_api_request
from flex.exceptions import ValidationError as FlexValidationError
from flex.http import Request

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408

logger = logging.getLogger(__name__)

RequestId = str


class Response:
    """Generic response object."""

    def __init__(self, status_code: int, message: bytes):
        """
        Initialize the response.

        :param status_code: the status code
        :param message: the message
        """
        self._status_code = status_code
        self._message = message

    @property
    def status_code(self) -> int:
        """Get the status code."""
        return self._status_code

    @property
    def message(self) -> bytes:
        """Get the message."""
        return self._message


class APISpec:
    """API Spec class to verify a request against an OpenAPI/Swagger spec."""

    def __init__(self, api_spec_path: Optional[str]):
        """
        Initialize the API spec.

        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """
        self._api_spec = None  # type Optional[Dict]
        if api_spec_path is not None:
            try:
                self._api_spec = load(api_spec_path)
            except FlexValidationError:
                logger.error(
                    "API specification YAML source file not correctly formatted."
                )

    def verify(self, request: Request) -> bool:
        """
        Verify a http_method, url and param against the provided API spec.

        :param request: the request object
        :return: whether or not the request conforms with the API spec
        """
        if self._api_spec is None:
            logger.debug("Skipping API verification!")
            return True

        try:
            validate_api_request(self._api_spec, request)
        except FlexValidationError:
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
        self.connection_id = connection_id
        self.restricted_to_protocols = restricted_to_protocols
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self.thread = None  # type: Optional[Thread]
        self.lock = Lock()
        self.is_stopped = True
        self._api_spec = APISpec(api_spec_path)
        self.timeout_window = timeout_window
        self.http_server = None  # type: Optional[HTTPServer]
        self.dispatch_ready_envelopes = {}  # type: Dict[RequestId, Envelope]
        self.timed_out_request_ids = set()  # type: Set[RequestId]

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
        else:
            self.dispatch_ready_envelopes.update({envelope.to: envelope})

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
            # turn request into envelope
            envelope = self.build_envelope(request)
            # send the envelope to the agent's inbox (via self.in_queue)
            self.in_queue.put_nowait(envelope)
            # wait for response envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes
            response_envelope = await self.get_response(envelope.sender)
            # turn response envelope into response
            response = self.build_response(response_envelope)
        else:
            response = Response(NOT_FOUND, b"Request Not Found")

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

    def build_envelope(self, request: Request) -> Envelope:
        """
        Process incoming API request by packaging into Envelope and sending it in-queue.

        The Envelope's message body contains the "performative", "path", "params", and "payload".

        :param http_method: the http method
        :param url: the url
        :param param: the parameter
        :param body: the body
        """
        client_id = uuid4().hex
        uri = URI(request.url)
        context = EnvelopeContext(connection_id=self.connection_id, uri=uri)
        # TODO: replace with HTTP protocol
        msg = {
            "performative": request.method,
            "path": request.path,
            "query": request.query,
            "payload": request.body,
        }
        msg_bytes = json.dumps(msg).encode()
        envelope = Envelope(
            to=self.address,
            sender=client_id,
            protocol_id=PublicId.from_str("fetchai/http:0.1.0"),
            context=context,
            message=msg_bytes,
        )
        return envelope

    def build_response(self, envelope: Optional[Envelope] = None) -> Response:
        if envelope is not None:
            # Response Envelope's msg will be a JSON with 'status_code', 'response', and 'payload' keys
            resp_msg = json.loads(envelope.message.decode())
            response = Response(resp_msg["status_code"], resp_msg["message"].encode())
        else:
            response = Response(REQUEST_TIMEOUT, b"Request Timeout")
        return response


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

        def get_url(self) -> str:
            """Get url."""
            url = "http://{}:{}{}".format(*self.server.server_address, self.path)
            return url

        def do_HEAD(self):
            """Deal with header only requests."""
            self.send_response(SUCCESS)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            request = self.build_request("get")

            future = asyncio.run_coroutine_threadsafe(
                self.channel.process(request), self.channel.loop
            )
            response = future.result()

            self.send_response(response.status_code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.message)

        def do_POST(self):
            """Respond to a POST request."""
            request = self.build_request("post")

            future = asyncio.run_coroutine_threadsafe(
                self.channel.process(request), self.channel.loop
            )
            response = future.result()

            self.send_response(response.status_code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.message)

        def build_request(self, method: str):
            content_length = self.headers["Content-Length"]
            body = (
                None
                if content_length is None
                else self.rfile.read(int(content_length)).decode()
            )
            request = Request(
                self.get_url(),
                method,
                content_type=self.headers.get_content_type(),
                body=body,
            )
            return request

    return HTTPHandler


class HTTPConnection(Connection):
    """Proxy to the functionality of the web RESTful API."""

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        api_spec_path: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize a connection to an RESTful API.

        :param address: the address of the agent.
        :param host: RESTful API hostname / IP address
        :param port: RESTful API port number
        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http", "0.1.0")

        super().__init__(*args, **kwargs)
        self.address = address
        self.channel = HTTPChannel(
            address,
            host,
            port,
            api_spec_path,
            connection_id=self.connection_id,
            restricted_to_protocols=kwargs.get("restricted_to_protocols", {}),
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
        cls, address: Address, connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from the connection configuration.

        :param address: the address of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        host = cast(str, connection_configuration.config.get("host"))
        port = cast(int, connection_configuration.config.get("port"))
        api_spec_path = cast(str, connection_configuration.config.get("api_spec_path"))

        restricted_to_protocols_names = {
            p.name for p in connection_configuration.restricted_to_protocols
        }
        excluded_protocols_names = {
            p.name for p in connection_configuration.excluded_protocols
        }
        return HTTPConnection(
            address,
            host,
            port,
            api_spec_path,
            connection_id=connection_configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )

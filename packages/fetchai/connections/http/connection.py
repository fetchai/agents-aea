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
from typing import Dict, Optional, Set, Tuple, cast
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import yaml

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI

SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408

logger = logging.getLogger(__name__)


class APIVerificationHelper:
    """API Verification Helper class to verify a request against an OpenAPI/Swagger spec."""

    def __init__(self, api_spec_path: Optional[str]):
        """
        Initialize the API verification helper.

        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """
        self.valid_paths = {}
        self.is_active = api_spec_path is not None
        if api_spec_path is not None:
            # TODO: the following api_spec format checks will be in their own function check_api (api_spec)
            try:
                with open(api_spec_path, "r") as f:
                    api_spec = yaml.safe_load(f)
            except FileNotFoundError:
                logger.error(
                    "API specification YAML source file not found. Please double-check filename and path."
                )
                return
            try:
                self.valid_paths = api_spec["paths"]
            except KeyError:
                logger.error("Key 'paths' not found in API spec.")
                return

    def verify(self, http_method: str, url: str, param: str) -> bool:
        """
        Verify a http_method, url and param against the provided API spec.

        :param http_method: the http method
        :param url: the url
        :param param: the parameter
        :return: whether or not the request conforms with the API spec
        """
        if not self.is_active:
            logger.debug("Skipping API verification!")
            return True
        path_key = url
        param_dict = json.loads(param)
        if param_dict != {}:
            param_key, param_value = list(param_dict.items())[0]
            param_value = param_value[0]
            path_key += r"/{" + param_key + r"}"
        method_key = http_method.lower()

        try:
            path_reconstruction_test = self.valid_paths[path_key][method_key]
            logger.debug("Verified path: {}".format(path_reconstruction_test))
        except KeyError:
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
        :param timeout_window: the timeout (in seconds) for a request to be handled.
        :param api_spec_path: Directory API path and filename of the API spec YAML source file.
        """
        self.address = address
        self.host = host
        self.port = port
        self.connection_id = connection_id
        self.restricted_to_protocols = restricted_to_protocols
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        # self.thread = Thread(target=self.receiving_loop)
        self.lock = Lock()
        self.stopped = True
        self._helper = APIVerificationHelper(api_spec_path)
        self.timeout_window = timeout_window
        self.http_server = None  # type: Optional[HTTPServer]
        self.dispatch_ready_envelopes = {}  # type: Dict[str, Envelope]

    @property
    def helper(self) -> APIVerificationHelper:
        """Get the api verification helper."""
        return self._helper

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

        self.dispatch_ready_envelopes.update({envelope.to: envelope})

    def connect(self):
        """
        Connect.

        Upon HTTP Channel connection, kickstart the HTTP Server in its own thread.
        """
        with self.lock:
            if self.stopped:
                try:
                    self.http_server = HTTPServer(
                        (self.host, self.port), HTTPHandlerFactory(self)
                    )
                    logger.info(
                        "HTTP Server has connected to port: {}.".format(self.port)
                    )
                    self.thread = Thread(target=self.http_server.serve_forever())
                    self.thread.start()
                    self.stopped = False
                except OSError:
                    logger.error(
                        "{}:{} is already in use, please try another Socket.".format(
                            self.host, self.port
                        )
                    )

    def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server and join the thread, then stop the channel.
        """
        assert self.http_server is not None, "Server not connected, call connect first!"

        with self.lock:
            if not self.stopped:
                self.http_server.shutdown()
                logger.info("HTTP Server has shutdown on port: {}.".format(self.port))
                self.stopped = True
                self.thread.join()

    async def process(
        self, http_method: str, url: str, param: str, body: Optional[str] = None,
    ) -> Tuple[int, str]:
        """
        Verify the request then send the request to Agent as an envelope.

        :param http_method: the http method
        :param url: the url
        :param param: the parameter
        :param body: the body
        :return: a tuple of response code and response description
        """
        valid_request = self.helper.verify(http_method, url, param)

        if valid_request:
            # _envelope = self.build_envelope(http_method, url, param, body)
            # Send the Envelope to the Agent's InBox (self.in_queue)
            # Wait for response Envelope within given timeout window (self.timeout_window) to appear in dispatch_ready_envelopes
            """
            if resp_envelop is not None:
                # Response Envelope's msg will be a JSON with 'status_code', 'response', and 'payload' keys
                resp_msg = json.loads(resp_envelop.message.decode())
                status_code = resp_msg["status_code"]
                raw_response = resp_msg["response"]
                body = resp_msg["payload"]
            else:
                status_code = REQUEST_TIMEOUT
                raw_response = "Request Timeout"
            """
        else:
            response_code = NOT_FOUND
            raw_response = "Request Not Found"

        response_desc = "\n\nResponse: {}\nStatus: ".format(raw_response)
        return response_code, response_desc

    def build_envelope(
        self, http_method: str, url: str, param: str, body: Optional[str] = None
    ) -> Envelope:
        """
        Process incoming API request by packaging into Envelope and sending it in-queue.

        The Envelope's message body contains the "performative", "path", "params", and "payload".

        :param http_method: the http method
        :param url: the url
        :param param: the parameter
        :param body: the body
        """
        client_id = uuid4().hex
        uri = URI("http://{}:{}{}".format(self.host, self.port, url))
        context = EnvelopeContext(connection_id=self.connection_id, uri=uri)
        # TODO: replace with HTTP protocol
        msg = {
            "performative": http_method,
            "path": url,
            "params": param,
            "payload": body,
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
            """Deal with ..."""
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            parsed_path = urlparse(self.path)
            url = parsed_path.path
            param = parse_qs(parsed_path.query)
            param = json.dumps(param)

            response_code, response_desc = self.channel.loop.call_soon_threadsafe(
                self.channel.process, "GET", url, param
            )

            # Wfile write: for additional response description.
            self.wfile.write(response_desc.encode())
            self.send_response(response_code)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_POST(self):
            """Respond to a POST request."""
            parsed_path = urlparse(self.path)
            url = parsed_path.path
            param = parse_qs(parsed_path.query)
            param = json.dumps(param)
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length).decode()

            response_code, response_desc = self.channel.loop.call_soon_threadsafe(
                self.channel.process, "POST", url, param, body
            )

            # Wfile write: for additional response description.
            self.wfile.write(response_desc.encode())
            self.send_response(response_code)
            self.send_header("Content-type", "text/html")
            self.end_headers()

    return HTTPHandler


class HTTPConnection(Connection):
    """Proxy to the functionality of the web RESTful API."""

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        api_spec_path: Optional[str] = None,  # Directory path of the API YAML file.
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

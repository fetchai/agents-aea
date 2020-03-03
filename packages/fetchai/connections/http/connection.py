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
import threading
import time

# from asyncio import CancelledError
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Tuple, cast
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


class HTTPChannel:
    """A wrapper for an RESTful API with an internal HTTPServer."""

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        api_spec_path: Optional[str],
        connection_id: PublicId,
    ):
        """
        Initialize a channel and process the initial API specification from the file path (if given).

        :param address: the address

        Note: In this current iteration, the HTTPChannel will package API specification into an envelope
              to initialize a local helper object called APIVerificationHelper. It emulates the function of
              an "echo" Skill handler. In future iterations, this envelope will be sent in-queue to be picked
              up by the Multiplexer itself to be carried downstream to its intended destination.
        """
        self.address = address
        self.host = host
        self.port = port
        self.connection_id = connection_id
        self.protocol_id = PublicId.from_str("fetchai/http:0.1.0")
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        # self.thread = Thread(target=self.receiving_loop)
        self.lock = threading.Lock()
        self.stopped = True
        # It is possible that env need to be stored as self.api_spec_envelope so that it can be sent
        #    upon connection and self.loop has been initialized.
        self._helper = APIVerificationHelper(api_spec_path)

    def _process_request(
        self, http_method: str, url: str, param: str, body: str = "{}"
    ) -> Envelope:
        """Process incoming API request by packaging into Envelope and sending it in-queue.

        The Envelope's message body contains the "performative", "path", "params", and "payload".
        """
        # Prepare the invididual contents of the Envelope.
        self._client_id = uuid4().hex
        uri = URI(f"http://{self.host}:{self.port}{url}")
        context = EnvelopeContext(connection_id=self.connection_id, uri=uri)
        # Prepare the Envelope's message body and encode it into bytes.
        msg = {
            "performative": http_method,
            "path": url,
            "params": param,
            "payload": body,
        }
        msg_bytes = json.dumps(msg).encode()
        # Prepare the Envelope itself using the individual contents.
        envelope = Envelope(
            to=self.address,
            sender=self._client_id,
            protocol_id=self.protocol_id,
            context=context,
            message=msg_bytes,
        )
        return envelope

    def send(self, envelope: Envelope) -> None:
        """
        Send the envelope in_queue.

        :param envelope: the envelope
        :return: None
        """
        assert self.in_queue is not None, "Input queue not initialized."
        assert self.loop is not None, "Loop not initialized."
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    # Commented because: Incompatible return value type (got "Coroutine[Any, Any, Any]", expected "Optional[Envelope]") line 136
    # def receive(self, *args, **kwargs) -> Optional["Envelope"]:
    #     """
    #     Receive the envelope in_queue. Or in out_queue?

    #     :param envelope: the envelope
    #     :return: None
    #     """
    #     assert self.in_queue is not None
    #     try:
    #         # No await keyword as this is not an async function?
    #         envelope = self.in_queue.get()
    #         # envelope = await self.in_queue.get()
    #         # Why does envelope keep getting <coroutine object Queue.get> rather than just None?
    #         if envelope is None:
    #             return None  # pragma: no cover
    #         return envelope
    #     except CancelledError:  # pragma: no cover
    #         return None

    def connect(self):
        """
        Connect.

        Upon HTTP Channel connection, kickstart the HTTP Server.
        """
        with self.lock:
            if self.stopped:
                self.stopped = False
                # self.thread.start()
                # Initializing the internal HTTP server
                try:
                    self.httpd = HTTPServer(
                        (self.host, self.port), HTTPHandlerFactory(self)
                    )
                    # self.httpd = HTTPServer((self.host, self.port), handler)
                    logger.info(f"HTTP Server has connected to port {self.port}.")
                    self.httpd.serve_forever()
                except OSError:
                    logger.error(
                        f"{self.host}:{self.port} is already in use, please try another Socket."
                    )

    def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server and then HTTP Channel.
        """
        with self.lock:
            if not self.stopped:
                self.httpd.shutdown()
                logger.info(f"HTTP Server has shutdown on port {self.port}.")
                self.stopped = True
                # self.thread.join()


def HTTPHandlerFactory(channel: HTTPChannel):
    class HTTPHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self._channel = channel
            super(HTTPHandler, self).__init__(*args, **kwargs)

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def do_GET(self):
            """Respond to a GET request."""
            parsed_path = urlparse(self.path)
            url = parsed_path.path
            param = parse_qs(parsed_path.query)
            param = json.dumps(param)

            response_code, response_desc = self._process("GET", url, param)
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

            response_code, response_desc = self._process("POST", url, param, body)
            # Wfile write: for additional response description.
            self.wfile.write(response_desc.encode())
            self.send_response(response_code)
            self.send_header("Content-type", "text/html")
            self.end_headers()

        def _process(
            self,
            http_method: str,
            url: str,
            param: str,
            body: Optional[str] = r"{}",
            timeout_window: int = 5,
        ) -> Tuple[int, str]:
            """Verify the request then send the request to Agent as an envelope."""
            valid_request = self._channel._helper._verify(http_method, url, param)

            if valid_request:
                # Create Envelope
                req_envelope = self._channel._process_request(
                    http_method, url, param, body
                )
                # Send the Envelope to the Agent's InBox.
                assert (
                    self._channel.in_queue is not None
                ), "Input queue not initialized."
                assert self._channel.loop is not None, "Loop not initialized."
                self._channel.send(req_envelope)
                # Wait for response Envelope within given timeout window
                time.sleep(timeout_window)
                # Check for response Envelope in Agent's InBox again. Or OutBox?
                # Note: A handler (i.e. Skill) need to be written in order to finalize the following below.
                """
                resp_envelop = self._channel.receive()
                # Write the API response back to console
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
                # Respond "Reqeust Not Found" without sending Envelope
                status_code = NOT_FOUND
                raw_response = "Request Not Found"

            console_response = f"\n\nResponse: {raw_response}\nStatus: "
            return status_code, console_response

    return HTTPHandler


class APIVerificationHelper:
    def __init__(self, api_spec_path: Optional[str]):
        self.valid_paths = {}
        if api_spec_path is not None:
            # the following api_spec format checks will be in their own function check_api (api_spec)
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

    def _verify(self, http_method: str, url: str, param: str) -> bool:

        path_key = url
        param_dict = json.loads(param)
        if bool(param_dict):  # Check param dict is not empty
            param_key, param_value = list(param_dict.items())[0]
            param_value = param_value[0]
            path_key += r"/{" + param_key + r"}"
        method_key = http_method.lower()

        try:
            path_reconstruction_test = self.valid_paths[path_key][method_key]
            logger.debug(f"Verified path: {path_reconstruction_test}")
        except KeyError:
            return False
        return True


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

        :param api_spec_path: the directory path of the API specification YAML source file.
        :param provider_addr: the provider IP address.
        :param provider_port: the provider port.
        :param connection_id: the identifier of the connection object.
        :param restricted_to_protocols: the only supported protocols for this connection.
        :param excluded_protocols: the excluded protocols for this connection.
        """

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http", "0.1.0")

        super().__init__(*args, **kwargs)
        self.address = address
        self.channel = HTTPChannel(
            address, host, port, api_spec_path, connection_id=self.connection_id,
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

    # async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
    #     """
    #     Receive an envelope.

    #     :return: the envelope received, or None.
    #     """
    #     if not self.connection_status.is_connected:
    #         raise ConnectionError(
    #             "Connection not established yet. Please use 'connect()'."
    #         )  # pragma: no cover
    #     return self.channel.receive(*args, **kwargs)

    @classmethod
    def from_config(
        cls, address: Address, connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from the connection configuration.

        :param address: the address of the agent.
        :param connection_configuration: the connection configuration object.
            :host - RESTful API hostname / IP address
            :port - RESTful API port number
            :api_spec_path - Directory API path and filename of the API spec YAML source file.
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

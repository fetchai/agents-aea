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
import logging
import threading
import time
import yaml
import json
from uuid import uuid4
from asyncio import CancelledError
# from threading import Thread
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional, Set, cast
from http.server import HTTPServer, BaseHTTPRequestHandler

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI

logger = logging.getLogger(__name__)


class HTTPChannel:
    """A wrapper for an RESTful API with an internal HTTPServer."""

    def __init__(self,
                 address: Address,
                 host: str,
                 port: int,
                 api_spec: str,
                 connection_id: PublicId,
                 excluded_protocols: Optional[Set[PublicId]] = None,
                 ):
        """
        Initialize a channel.

        :param address: the address
        """
        self.address = address
        self.host = host
        self.port = port
        self.connection_id = connection_id
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self.excluded_protocols = excluded_protocols
        # self.thread = Thread(target=self.receiving_loop)
        self.lock = threading.Lock()
        self.stopped = True

        if api_spec is not None:
            self._process_api(api_spec)
        logger.info(f"Initialized the HTTP Server on HOST: {host} and PORT: {port}")

    def _process_api(self, api_spec):
        """Process the api_spec.

        Decode all paths to get envelops each, and put it in the agent's inbox.
        """
        try:
            paths = api_spec['paths']
        except KeyError:
            logger.error("Key 'paths' not found in API spec.")

        for path_name, path_value in paths.items():
            try:
                envelope = self._decode_path(path_name, path_value)
                assert self.in_queue is not None, "Input queue not initialized."
                assert self._loop is not None, "Loop not initialized."
                # Ok to put these Envelopes in_queue during HTTPChannel initialization?
                asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)
            except ValueError:
                logger.error(f"Bad formatted path: {path_name}")
            except Exception as e:
                logger.error(f"Error when processing a path. Message: {str(e)}")

    def _decode_path(self, path_name: str, path_value: dict, separator: str = '/'):
        """Path --> Envelope

        Convert specified API path name and value into in_queue'd Envelope.
        Envelope's msg consists of the response options for each REST req in path.
        """
        path_split = path_name.split(separator)

        to = path_split[1].strip()  # to: name of Skill (petstoresim)?
        sender = 'TBD'  # hardcoded for now
        protocol_id = PublicId.from_str('fetchai/http:0.1.0')  # hardcoded for now
        uri = URI(f"http://{self.host}:{self.port}{path_name}")
        context = EnvelopeContext(connection_id=self.connection_id, uri=uri)
        # Msg consists of all of the responses for each REST req in JSON format.
        responses = {}
        for req_type, req_value in path_value.items():
            responses[req_type] = req_value['responses']
        message = json.dumps(responses).decode("utf-8").strip()

        return Envelope(to=to, sender=sender, protocol_id=protocol_id,
                        message=message, context=context)

    def _process_request(self, http_method: str, url: str, param: str, body: str = '{}'):
        """Process incoming API request by packaging into Envelope and sending it in-queue.

        """
        self._client_id = uuid4().hex
        protocol_id = PublicId.from_str('fetchai/http:0.1.0')
        uri = URI(f"http://{self.host}:{self.port}{url}")
        context = EnvelopeContext(connection_id=self.connection_id, uri=uri)
        # Prepare the Envelope's message body and encode it into bytes.
        msg = {
            'performative': http_method,
            'path': url,
            'params': param,
            'payload': body,
        }
        msg_bytes = json.dumps(msg).encode()
        # Prepare the Envelope itself using the provided variables.
        envelope = Envelope(
            to=self.address,
            sender=self._client_id,
            protocol_id=protocol_id,
            context=context,
            message=msg_bytes,
        )
        # Send the Envelope to the Agent's InBox.
        asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop)

    def _send_response():
        """Pass the response from out-bounded Envelope back to the front-end client.

        Currently, the response will be written back in the cmd terminal.
        """
        # self.wfile.write(self.path.encode())
        pass

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
                    # self.httpd = HTTPServer((self.host, self.port), HTTPHandler(self))
                    # handler = SimpleHTTPServer.SimpleHTTPRequestHandler
                    # handler = HTTPHandler.set_channel(self)
                    # handler.set_channel(self)
                    self.httpd = HTTPServer((self.host, self.port), HTTPHandlerFactory(self))
                    # self.httpd = HTTPServer((self.host, self.port), handler)
                    logger.debug(f"HTTP Server has connected to port {self.port}.")
                    self.httpd.serve_forever()
                except OSError:
                    logger.error(f"{host}:{port} is already in use, please try another Socket.")

    def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server and then HTTP Channel.
        """
        with self.lock:
            if not self.stopped:
                self.httpd.server_close()
                print(f"Server shutdown from port {PORT}.")
                self.httpd.shutdown()
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
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            parsed_path = urlparse(self.path)
            url = parsed_path.path
            # url = parsed_path.geturl()
            param = parse_qs(parsed_path.query)
            param = json.dumps(param)

            self._channel._process_request('GET', url, param)

        def do_POST(self):
            """Respond to a POST request."""
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            parsed_path = urlparse(self.path)
            url = parsed_path.path
            # url = parsed_path.geturl()
            param = parse_qs(parsed_path.query)
            param = json.dumps(param)

            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode()

            self._channel._process_request('POST', url, param, body)

    return HTTPHandler


class HTTPConnection(Connection):
    """Proxy to the functionality of the web RESTful API."""

    def __init__(self,
                 address: Address,
                 host: str = '',
                 port: int = 10000,
                 api_path: str = None,  # Directory path of the API YAML file.
                 *args,
                 **kwargs
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

        # the following api_spec format checks will be in their own function check_api(api_spec)
        if api_path is not None:
            try:
                with open(api_path, 'r') as f:
                    api_spec = yaml.safe_load(f)
            except FileNotFoundError:
                logger.error("API specification YAML source file not found. Please double-check filename and path.")
                return
        else:
            api_spec = api_path

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http", "0.1.0")

        super().__init__(*args, **kwargs)
        self.address = address
        self.channel = HTTPChannel(address, host, port, api_spec,
                                   connection_id=self.connection_id,
                                   excluded_protocols=self.excluded_protocols
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
            :host - RESTful API hostname / IP address
            :port - RESTful API port number
            :api - Directory API path and filename of the API spec YAML source file.
        :return: the connection object
        """
        host = cast(str, connection_configuration.config.get("host"))
        port = cast(int, connection_configuration.config.get("port"))
        api = cast(str, connection_configuration.config.get("api")) if not '' else None

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
            api,
            connection_id=connection_configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )

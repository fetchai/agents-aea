# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 Fetch.AI Limited
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

"""HTTP connection, channel, and server"""

import asyncio
import logging
import threading
import time
import yaml
import json
from asyncio import CancelledError
from threading import Thread
from typing import Any, Dict, List, Optional, Set, cast
from http.server import HTTPServer, BaseHTTPRequestHandler

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope, EnvelopeContext, URI


logger = logging.getLogger(__name__)


class HTTPHandler(BaseHTTPRequestHandler):

    def do_HEAD(s):
        # Placeholder functions
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        """Respond to a GET request."""
        # Placeholder functions
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Title goes here.</title></head>")
        s.wfile.write("<body><p>This is a test.</p>")
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        s.wfile.write("<p>You accessed path: %s</p>" % s.path)
        s.wfile.write("</body></html>")

    def do_POST(s):
        """Respond to a GET request."""
        pass


class HTTPChannel:
    """A wrapper for an RESTful API with an internal HTTPServer."""

    def __init__(self,
                 # address: Address,
                 api_spec: str,
                 host: str,
                 port: int,
                 excluded_protocols: Optional[Set[PublicId]] = None,
                 ):
        """
        Initialize a channel.

        :param address: the address
        """
        # self.address = address
        self.host = host
        self.port = port
        # self.uri_base = f"http://{host}:{port}"
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self.excluded_protocols = excluded_protocols
        self.thread = Thread(target=self.receiving_loop)
        self.lock = threading.Lock()
        self.stopped = True
        # Initializing the internal HTTP server
        try:
            self.server = HTTPServer((self.host, self.port), HTTPHandler)
        except OSError:
            logger.error(f"{host}:{port} is already in use, please try another Socket.")
        # Process API specifications into Envelopes to be sent to InBox
        self._process_api(api_spec)
        logger.info("Initialized the HTTP Server.")

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
                envelope = _decode_path(path_name, path_value)
                assert self.in_queue is not None, "Input queue not initialized."
                assert self._loop is not None, "Loop not initialized."
                # Ok to put these Envelopes in_queue during HTTPChannel initialization?
                asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self._loop)
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
        context = EnvelopeContext(connection_id=self._connection_id, uri=uri)
        # Msg consists of all of the responses for each REST req in JSON format.
        responses = {}
        for req_type, req_value in path_value.items():
            responses[req_type] = req_value['responses']
        message = json.dumps(responses).decode("utf-8").strip()

        return Envelope(to=to, sender=sender, protocol_id=protocol_id,
                        message=message, context=context)

    def connect(self):
        """
        Connect.

        Upon HTTP Channel connection, kickstart the HTTP Server.
        """
        with self.lock:
            if self.stopped:
                self.stopped = False
                self.thread.start()
                self.server.serve_forever()
                logger.debug("HTTP Server has started..")
                # self._httpCall = HTTPCalls(
                #     server_address=self.provider_addr, port=self.provider_port
                # )
                # self.stopped = False
                # self.thread.start()
                # logger.debug("HTTP Channel is connected.")
                # self.try_register()

    def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes.

        :param envelope: the envelope
        :return: None
        """
        # TO-DO: Replace httpCall with HTTPHandler
        pass
        # assert self._httpCall is not None

        # if self.excluded_protocols is not None:
        #     if envelope.protocol_id in self.excluded_protocols:
        #         logger.error(
        #             "This envelope cannot be sent with the oef connection: protocol_id={}".format(
        #                 envelope.protocol_id
        #             )
        #         )
        #         raise ValueError("Cannot send message.")

        # self._httpCall.send_message(
        #     sender_address=envelope.sender,
        #     receiver_address=envelope.to,
        #     protocol=str(envelope.protocol_id),
        #     context=b"None",
        #     payload=envelope.message,
        # )

    def receiving_loop(self) -> None:
        """Receive the messages from the provider."""
        # TO-DO: Replace httpCall with HTTPHandler
        pass
        # assert self._httpCall is not None
        # assert self.in_queue is not None
        # assert self.loop is not None
        # while not self.stopped:
        #     messages = self._httpCall.get_messages(
        #         sender_address=self.address
        #     )  # type: List[Dict[str, Any]]
        #     for message in messages:
        #         logger.debug("Received message: {}".format(message))
        #         envelope = Envelope(
        #             to=message["TO"]["RECEIVER_ADDRESS"],
        #             sender=message["FROM"]["SENDER_ADDRESS"],
        #             protocol_id=PublicId.from_str(message["PROTOCOL"]),
        #             message=message["PAYLOAD"],
        #         )
        #         self.loop.call_soon_threadsafe(self.in_queue.put_nowait, envelope)
        #     time.sleep(0.5)
        # logger.debug("Receiving loop stopped.")

    def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off the HTTP Server and then HTTP Channel thread.
        """
        assert self._httpCall is not None
        with self.lock:
            if not self.stopped:
                self.server.server_close()
                self.server.shutdown()  # Need to double-check that this is the right approach to shutdown server.
                self.stopped = True
                self.thread.join()
                # self._httpCall.unregister(self.address)
                # self._httpCall.disconnect()
                # self.stopped = True
                # self.thread.join()


class HTTPConnection(Connection):
    """Proxy to the functionality of the web RESTful API."""

    def __init__(self,
                 # address: Address,
                 api_path: str,  # Directory path of the API YAML file.
                 host: str,
                 port: int = 10000,
                 *args,
                 **kwargs
                 ):
        """
        Initialize a connection to an RESTful API.

        :param address: the address used in the protocols.
        :param api_spec_path: the directory path of the API specification YAML source file.
        :param provider_addr: the provider IP address.
        :param provider_port: the provider port.
        :param connection_id: the identifier of the connection object.
        :param restricted_to_protocols: the only supported protocols for this connection.
        :param excluded_protocols: the excluded protocols for this connection.
        """

        # the following api_spec format checks will be in their own function check_api(api_spec)
        try:
            with open(api_path, 'r') as f:
                api_spec = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error("API specification YAML source file not found. Please double-check filename and path.")
            return

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http", "0.1.0")
        super().__init__(*args, **kwargs)
        # self.address = address
        self.channel = HTTPChannel(api_spec, host, port, excluded_protocols=self.excluded_protocols)  # type: ignore


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
        cls, connection_configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the HTTP connection from the connection configuration.

        :param connection_configuration: the connection configuration object.
            :host - RESTful API hostname / IP address
            :port - RESTful API port number
            :api - Directory path and filename of the API spec YAML source file.
        :return: the connection object
        """
        addr = cast(str, connection_configuration.config.get("host"))
        port = cast(int, connection_configuration.config.get("port"))
        api_path = cast(str, connection_configuration.config.get("api"))

        restricted_to_protocols_names = {
            p.name for p in connection_configuration.restricted_to_protocols
        }
        excluded_protocols_names = {
            p.name for p in connection_configuration.excluded_protocols
        }
        return HTTPConnection(
            # address,
            api_path,
            host,
            port,
            connection_id=connection_configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )

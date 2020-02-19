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

"""HTTP connection and channel."""

import asyncio
import logging
import threading
import time
import json
import yaml
from asyncio import CancelledError
from threading import Thread
from typing import Any, Dict, List, Optional, Set, cast

from fetch.p2p.api.http_calls import HTTPCalls

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.helpers.base import locate
from aea.mail.base import AEAConnectionError, Address, Envelope, EnvelopeContext

logger = logging.getLogger(__name__)


class HTTPChannel:
    """A wrapper for an RESTful API."""

    def __init__(
        self,
        address: Address,
        api_spec: str,
        provider_addr: str,
        provider_port: int,
        excluded_protocols: Optional[Set[PublicId]] = None,
    ):
        """
        Initialize a channel.

        :param address: the address
        """
        self.address = address
        self.provider_addr = provider_addr
        self.provider_port = provider_port
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self._httpCall = None  # type: Optional[HTTPCalls]
        self.excluded_protocols = excluded_protocols
        self.thread = Thread(target=self.receiving_loop)
        self.lock = threading.Lock()
        self.stopped = True
        logger.info("Initialised the http channel")

    def connect(self):
        """
        Connect.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        with self.lock:
            if self.stopped:
                pass
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
        assert self._httpCall is not None

        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:
                logger.error(
                    "This envelope cannot be sent with the oef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")

        # self._httpCall.send_message(
        #     sender_address=envelope.sender,
        #     receiver_address=envelope.to,
        #     protocol=str(envelope.protocol_id),
        #     context=b"None",
        #     payload=envelope.message,
        )

    def receiving_loop(self) -> None:
        """Receive the messages from the provider."""
        assert self._httpCall is not None
        assert self.in_queue is not None
        assert self.loop is not None
        while not self.stopped:
            messages = self._httpCall.get_messages(
                sender_address=self.address
            )  # type: List[Dict[str, Any]]
            for message in messages:
                logger.debug("Received message: {}".format(message))
                envelope = Envelope(
                    to=message["TO"]["RECEIVER_ADDRESS"],
                    sender=message["FROM"]["SENDER_ADDRESS"],
                    protocol_id=PublicId.from_str(message["PROTOCOL"]),
                    message=message["PAYLOAD"],
                )
                self.loop.call_soon_threadsafe(self.in_queue.put_nowait, envelope)
            time.sleep(0.5)
        logger.debug("Receiving loop stopped.")

    def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        assert self._httpCall is not None
        with self.lock:
            if not self.stopped:
                self._httpCall.unregister(self.address)
                # self._httpCall.disconnect()
                self.stopped = True
                self.thread.join()


class HTTPConnection(Connection):
    """Proxy to the functionality of the RESTful API."""

    def __init__(self,
                 address: Address,
                 api_spec_path: str,  # Directory path of the API YAML file.
                 provider_addr: str,
                 provider_port: int = 10000,
                 *args,
                 **kwargs
                 ):
        """
        Initialize a connection to an RESTful API.

        :param address: the address used in the protocols.
        """

        # the following api_spec format checks will be in their own function check_api(api_spec)
        api_spec = yaml.safe_load(api_spec_path)

        try:
            self.validator.validate(instance=configuration_file_json)
        except Exception:
            raise

        try:
            json.loads(api_spec)
        except json.JSONDecodeError:
            print("api_spec is not in proper JSON format.")

        if kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "http", "0.1.0")
        super().__init__(*args, **kwargs)
        self.address = address
        self.channel = HTTPChannel(address, api_spec, provider_addr, provider_port,
                                   excluded_protocols=self.excluded_protocols)  # type: ignore

    async def connect(self) -> None:
        """
        Connect to the gym.

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
            :addr - RESTful API address
            :port - RESTful API port
            :api - Directory path and filename of the API spec YAML source file.
        :return: the connection object
        """
        addr = cast(str, connection_configuration.config.get("addr"))
        port = cast(int, connection_configuration.config.get("port"))
        api_spec_path = cast(str, connection_configuration.config.get("api"))

        restricted_to_protocols_names = {
            p.name for p in connection_configuration.restricted_to_protocols
        }
        excluded_protocols_names = {
            p.name for p in connection_configuration.excluded_protocols
        }
        return HTTPConnection(
            address,
            api_spec_path,
            addr,
            port,
            connection_id=connection_configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )

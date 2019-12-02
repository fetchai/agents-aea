# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""Peer to Peer connection and channel."""

# TODO: reintroduce p2p and add api
import asyncio
import logging
import threading
import time
from asyncio import CancelledError
from threading import Thread
from typing import Optional, cast, Dict, List, Any, Set

from fetch.p2p.api.http_calls import HTTPCalls

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.mail.base import Envelope, AEAConnectionError

logger = logging.getLogger(__name__)


class PeerToPeerChannel:
    """A wrapper for an SDK or API."""

    def __init__(self, public_key: str, provider_addr: str, provider_port: int):
        """
        Initialize a channel.

        :param public_key: the public key
        """
        self.public_key = public_key
        self.provider_addr = provider_addr
        self.provider_port = provider_port
        self.in_queue = None  # type: Optional[asyncio.Queue]
        self.loop = None  # type: Optional[asyncio.AbstractEventLoop]
        self._httpCall = None  # type: Optional[HTTPCalls]

        self.thread = Thread(target=self.receiving_loop)
        self.lock = threading.Lock()
        self.stopped = True
        logger.info("Initialised the peer to peer channel")

    def connect(self):
        """
        Connect.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        with self.lock:
            if self.stopped:
                self._httpCall = HTTPCalls(server_address=self.provider_addr, port=self.provider_port)
                self.stopped = False
                self.thread.start()
                logger.debug("P2P Channel is connected.")
                self.try_register()

    def try_register(self) -> bool:
        """Try to register to the provider."""
        try:
            logger.info(self.public_key)
            query = self._httpCall.register(sender_address=self.public_key, mailbox=True)
            return query['status'] == "OK"
        except Exception:
            logger.warning("Could not register to the provider.")
            raise AEAConnectionError()

    def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes.

        :param envelope: the envelope
        :return: None
        """
        self._httpCall.send_message(sender_address=envelope.sender,
                                    receiver_address=envelope.to,
                                    protocol=envelope.protocol_id,
                                    context=b"None",
                                    payload=envelope.message)

    def receiving_loop(self) -> None:
        """Receive the messages from the provider."""
        while not self.stopped:
            messages = self._httpCall.get_messages(sender_address=self.public_key)  # type: List[Dict[str, Any]]
            for message in messages:
                logger.debug("Received message: {}".format(message))
                envelope = Envelope(to=message['TO']['RECEIVER_ADDRESS'],
                                    sender=message['FROM']['SENDER_ADDRESS'],
                                    protocol_id=message['PROTOCOL'],
                                    message=message['PAYLOAD'])
                asyncio.run_coroutine_threadsafe(self.in_queue.put(envelope), self.loop).result()
            time.sleep(0.5)
        logger.debug("Receiving loop stopped.")

    def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        with self.lock:
            if not self.stopped:
                self._httpCall.unregister(self.public_key)
                # self._httpCall.disconnect()
                self.stopped = True
                self.thread.join()


class PeerToPeerConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    restricted_to_protocols = set()  # type: Set[str]

    def __init__(self, public_key: str, provider_addr: str, provider_port: int = 8000, connection_id: str = "p2p",
                 restricted_to_protocols: Optional[Set[str]] = None):
        """
        Initialize a connection to an SDK or API.

        :param public_key: the public key used in the protocols.
        """
        super().__init__(connection_id=connection_id, restricted_to_protocols=restricted_to_protocols)
        self.channel = PeerToPeerChannel(public_key, provider_addr, provider_port)
        self.public_key = public_key

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
        Disconnect from P2P.

        :return: None
        """
        if self.connection_status.is_connected:
            self.connection_status.is_connected = False
            self.channel.disconnect()
            self.stop()

    async def send(self, envelope: 'Envelope') -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        if not self.connection_status.is_connected:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self.channel.send(envelope)

    async def receive(self, *args, **kwargs) -> Optional['Envelope']:
        """
        Receive an envelope.

        :return: the envelope received, or None.
        """
        if not self.connection_status.is_connected:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        try:
            envelope = await self.channel.in_queue.get()
            if envelope is None:
                return

            return envelope
        except CancelledError:
            return None

    def stop(self) -> None:
        """
        Tear down the connection.

        :return: None
        """
        self.channel.disconnect()

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the P2P connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        addr = cast(str, connection_configuration.config.get("addr"))
        port = cast(int, connection_configuration.config.get("port"))
        return PeerToPeerConnection(public_key, addr, port,
                                    restricted_to_protocols=set(connection_configuration.restricted_to_protocols))

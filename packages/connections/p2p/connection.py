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
import logging
import queue
from queue import Queue
from threading import Thread
from typing import Optional, cast, Dict, List, Any

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Channel, Connection
from aea.mail.base import Envelope

from fetch.p2p.api.http_calls import HTTPCalls

logger = logging.getLogger(__name__)


class PeerToPeerChannel(Channel):
    """A wrapper for an SDK or API."""

    def __init__(self, public_key: str, provider_addr: str, provider_port: int):
        """
        Initialize a channel.

        :param public_key: the public key
        """
        self.public_key = public_key
        self.provider_addr = provider_addr
        self.provider_port = provider_port
        self.in_queue = Queue()  # type: Queue
        self._httpCall = None  # type: HTTPCalls
        logger.info("Initialised the peer to peer channel")

    def connect(self) -> Optional[Queue]:
        """
        Connect.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        self._httpCall = HTTPCalls(server_address=self.provider_addr, port=self.provider_port)
        logger.info("Connected")
        self.try_register()
        return self.in_queue

    def try_register(self) -> bool:
        """Try to register to the provider."""
        try:
            logger.info(self.public_key)
            query = self._httpCall.register(sender_address=self.public_key, mailbox=True)
            return query['status'] == "OK"
        except Exception:
            logger.warning("Could not register to the provider.")
            return False

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

    def receive(self) -> None:
        """Receive the messages from the provider."""
        messages = self._httpCall.get_messages(sender_address=self.public_key)  # type: List[Dict[str, Any]]
        for message in messages:
            logger.info(message)
            envelope = Envelope(to=message['TO']['RECEIVER_ADDRESS'],
                                sender=message['FROM']['SENDER_ADDRESS'],
                                protocol_id=message['PROTOCOL'],
                                message=message['PAYLOAD'])
            self.in_queue.put(envelope)

    def disconnect(self) -> None:
        """
        Disconnect.

        :return: None
        """
        self._httpCall.unregister(self.public_key)
        self._httpCall.disconnect()


class PeerToPeerConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    def __init__(self, public_key: str, provider_addr: str, provider_port: int = 8000):
        """
        Initialize a connection to an SDK or API.

        :param public_key: the public key used in the protocols.
        """
        super().__init__()
        self.public_key = public_key

        self.channel = PeerToPeerChannel(public_key, provider_addr, provider_port)
        self._connection = None  # type: Optional[Queue]
        self.in_thread = None  # type: Optional[Thread]
        self.out_thread = None  # type: Optional[Thread]

    def _fetch(self) -> None:
        """
        Fetch the envelopes from the outqueue and send them.

        :return: None
        """
        while self.connection_status.is_connected:
            try:
                envelope = self.out_queue.get(block=True, timeout=2.0)
                self.send(envelope)
            except queue.Empty:
                pass

    def _receive_loop(self) -> None:
        """
        Receive messages.

        :return: None
        """
        assert self._connection is not None, "Call connect before calling _receive_loop."
        while self.connection_status.is_connected:
            try:
                self.channel.receive()
                envelope = self._connection.get(timeout=2.0)
                self.in_queue.put_nowait(envelope)
            except queue.Empty:
                pass

    def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.connection_status.is_connected = True
            self._connection = self.channel.connect()
            self.in_thread = Thread(target=self._receive_loop)
            self.out_thread = Thread(target=self._fetch)
            self.in_thread.start()
            self.out_thread.start()

    def disconnect(self) -> None:
        """
        Disconnect from the gym.

        :return: None
        """
        assert self.in_thread is not None, "Call connect before disconnect."
        assert self.out_thread is not None, "Call connect before disconnect."
        if self.connection_status.is_connected:
            self.connection_status.is_connected = False
            self.in_thread.join()
            self.out_thread.join()
            self.in_thread = None
            self.out_thread = None
            self.channel.disconnect()
            self.stop()

    def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        :return: None
        """
        if not self.connection_status.is_connected:
            raise ConnectionError("Connection not established yet. Please use 'connect()'.")
        self.channel.send(envelope)

    def stop(self) -> None:
        """
        Tear down the connection.

        :return: None
        """
        self._connection = None

    @classmethod
    def from_config(cls, public_key: str, connection_configuration: ConnectionConfig) -> 'Connection':
        """
        Get the Gym connection from the connection configuration.

        :param public_key: the public key of the agent.
        :param connection_configuration: the connection configuration object.
        :return: the connection object
        """
        addr = cast(str, connection_configuration.config.get("addr"))
        port = cast(int, connection_configuration.config.get("port"))
        return PeerToPeerConnection(public_key, addr, port)

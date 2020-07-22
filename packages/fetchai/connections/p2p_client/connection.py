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

import asyncio
import logging
import threading
import time
from asyncio import CancelledError
from threading import Thread
from typing import Any, Dict, List, Optional, Set, cast

from fetch.p2p.api.http_calls import HTTPCalls

from aea.configurations.base import PublicId
from aea.connections.base import Connection
from aea.mail.base import AEAConnectionError, Address, Envelope

logger = logging.getLogger("aea.packages.fetchai.connections.p2p_client")

PUBLIC_ID = PublicId.from_str("fetchai/p2p_client:0.4.0")


class PeerToPeerChannel:
    """A wrapper for an SDK or API."""

    def __init__(
        self,
        address: Address,
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
        self.logger = logger
        self.logger.info("Initialised the peer to peer channel")

    def connect(self):
        """
        Connect.

        :return: an asynchronous queue, that constitutes the communication channel.
        """
        with self.lock:
            if self.stopped:
                self._httpCall = HTTPCalls(
                    server_address=self.provider_addr, port=self.provider_port
                )
                self.stopped = False
                self.thread.start()
                self.logger.debug("P2P Channel is connected.")
                self.try_register()

    def try_register(self) -> bool:
        """Try to register to the provider."""
        try:
            assert self._httpCall is not None
            self.logger.info(self.address)
            query = self._httpCall.register(sender_address=self.address, mailbox=True)
            return query["status"] == "OK"
        except Exception:  # pragma: no cover
            self.logger.warning("Could not register to the provider.")
            raise AEAConnectionError()

    def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes.

        :param envelope: the envelope
        :return: None
        """
        assert self._httpCall is not None

        if self.excluded_protocols is not None:
            if envelope.protocol_id in self.excluded_protocols:  # pragma: nocover
                self.logger.error(
                    "This envelope cannot be sent with the oef connection: protocol_id={}".format(
                        envelope.protocol_id
                    )
                )
                raise ValueError("Cannot send message.")

        self._httpCall.send_message(
            sender_address=envelope.sender,
            receiver_address=envelope.to,
            protocol=str(envelope.protocol_id),
            context=b"None",
            payload=envelope.message,
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
                self.logger.debug("Received message: {}".format(message))
                envelope = Envelope(
                    to=message["TO"]["RECEIVER_ADDRESS"],
                    sender=message["FROM"]["SENDER_ADDRESS"],
                    protocol_id=PublicId.from_str(message["PROTOCOL"]),
                    message=message["PAYLOAD"],
                )
                self.loop.call_soon_threadsafe(self.in_queue.put_nowait, envelope)
            time.sleep(0.5)
        self.logger.debug("Receiving loop stopped.")

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


class PeerToPeerClientConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize a connection to an SDK or API."""
        super().__init__(**kwargs)
        addr = cast(str, self.configuration.config.get("addr"))
        port = cast(int, self.configuration.config.get("port"))
        assert addr is not None and port is not None, "addr and port must be set!"
        self.channel = PeerToPeerChannel(self.address, addr, port, excluded_protocols=self.excluded_protocols)  # type: ignore

    async def connect(self) -> None:
        """
        Connect to the gym.

        :return: None
        """
        if not self.connection_status.is_connected:
            self.channel.logger = self.logger
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

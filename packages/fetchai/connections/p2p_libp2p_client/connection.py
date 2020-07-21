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

"""This module contains the libp2p client connection."""

import asyncio
import logging
import random
import struct
from asyncio import AbstractEventLoop, CancelledError
from random import randint
from typing import List, Optional, Union, cast

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.crypto.registries import make_crypto
from aea.mail.base import Envelope

logger = logging.getLogger("aea.packages.fetchai.connections.p2p_libp2p_client")

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p_client:0.4.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]


class Uri:
    """
    Holds a node address in format "host:port"
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        if uri is not None:
            split = uri.split(":", 1)
            self._host = split[0]
            self._port = int(split[1])
        elif host is not None and port is not None:
            self._host = host
            self._port = port
        else:
            self._host = "127.0.0.1"
            self._port = randint(5000, 10000)  # nosec
            # raise ValueError("Either 'uri' or both 'host' and 'port' must be set")

    def __str__(self):
        return "{}:{}".format(self._host, self._port)

    def __repr__(self):  # pragma: no cover
        return self.__str__()

    @property
    def host(self) -> str:
        """Get host."""
        return self._host

    @property
    def port(self) -> int:
        """Get port."""
        return self._port


class P2PLibp2pClientConnection(Connection):
    """
    A libp2p client connection.
    Send and receive envelopes to and from agents on the p2p network without deploying a libp2p node.
    Connect to the libp2p node using traffic delegation service.
    """

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """
        Initialize a libp2p client connection.
        """
        super().__init__(**kwargs)

        ledger_id = self.configuration.config.get("ledger_id", DEFAULT_LEDGER)
        if ledger_id not in SUPPORTED_LEDGER_IDS:
            raise ValueError(  # pragma: nocover
                "Ledger id '{}' is not supported. Supported ids: '{}'".format(
                    ledger_id, SUPPORTED_LEDGER_IDS
                )
            )
        # TODO: ensure ledger_id matches with provided key of p2p node.

        key_file = self.configuration.config.get("client_key_file")  # Optional[str]
        nodes = self.configuration.config.get("nodes")

        assert nodes is not None, "At least one node should be provided"
        nodes = list(cast(List, nodes))

        nodes_uris = [node["uri"] for node in nodes]
        assert len(nodes_uris) == len(
            nodes
        ), "Delegate Uri should be provided for each node"

        if (
            self.has_crypto_store
            and self.crypto_store.crypto_objects.get(ledger_id, None) is not None
        ):  # pragma: no cover
            key = self.crypto_store.crypto_objects[ledger_id]
        elif key_file is not None:
            key = make_crypto(ledger_id, private_key_path=key_file)
        else:
            key = make_crypto(ledger_id)

        # client connection id
        self.key = key
        logger.debug("Public key used by libp2p client: {}".format(key.public_key))

        # delegate uris
        self.delegate_uris = [Uri(node_uri) for node_uri in nodes_uris]

        # delegates certificates
        # TOFIX(LR) will be mandatory
        self.delegate_certs = []

        # select a delegate
        index = random.randint(0, len(self.delegate_uris) - 1)  # nosec
        self.node_uri = self.delegate_uris[index]
        # self.node_cert = self.delegate_certs[index]
        logger.debug("Node to use as delegate: {}".format(self.node_uri))

        # tcp connection
        self._reader = None  # type: Optional[asyncio.StreamReader]
        self._writer = None  # type: Optional[asyncio.StreamWriter]

        self._loop = None  # type: Optional[AbstractEventLoop]
        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._process_messages_task = None  # type: Union[asyncio.Future, None]

    async def connect(self) -> None:
        """
        Set up the connection.

        :return: None
        """
        if self.connection_status.is_connected:  # pragma: no cover
            return
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        try:
            # connect libp2p client
            self.connection_status.is_connecting = True

            # connect the tcp socket
            self._reader, self._writer = await asyncio.open_connection(
                self.node_uri.host,
                self.node_uri._port,  # pylint: disable=protected-access
                loop=self._loop,
            )

            # send agent address to node
            await self._setup_connection()

            self.connection_status.is_connecting = False
            self.connection_status.is_connected = True

            self.logger.info(
                "Successfully connected to libp2p node {}".format(str(self.node_uri))
            )

            # start receiving msgs
            self._in_queue = asyncio.Queue()
            self._process_messages_task = asyncio.ensure_future(
                self._process_messages(), loop=self._loop
            )
        except (CancelledError, Exception) as e:
            self.connection_status.is_connected = False
            raise e

    async def _setup_connection(self):
        await self._send(bytes(self.address, "utf-8"))
        await self._receive()

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        assert (
            self.connection_status.is_connected or self.connection_status.is_connecting
        ), "Call connect before disconnect."
        self.connection_status.is_connected = False
        self.connection_status.is_connecting = False

        assert self._process_messages_task is not None
        assert self._writer is not None

        if self._process_messages_task is not None:
            self._process_messages_task.cancel()
            # TOFIX(LR) mypy issue https://github.com/python/mypy/issues/8546
            # self._process_messages_task = None

        self.logger.debug("disconnecting libp2p client connection...")
        self._writer.write_eof()
        await self._writer.drain()
        self._writer.close()
        # TOFIX(LR) requires python 3.7 minimum
        # await self._writer.wait_closed()

        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:  # pragma: no cover
            self.logger.debug("Called disconnect when input queue not initialized.")

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            assert self._in_queue is not None, "Input queue not initialized."
            data = await self._in_queue.get()
            if data is None:
                self.logger.debug("Received None.")
                if (
                    self._connection_status.is_connected
                    or self._connection_status.is_connecting
                ):
                    await self.disconnect()
                return None
                # TOFIX(LR) attempt restarting the node?
            self.logger.debug("Received data: {}".format(data))
            return Envelope.decode(data)
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: no cover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        await self._send(envelope.encode())

    async def _process_messages(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        while True:
            data = await self._receive()
            assert self._in_queue is not None, "Input queue not initialized."
            self._in_queue.put_nowait(data)
            if data is None:
                break

    async def _send(self, data: bytes) -> None:
        assert self._writer is not None
        size = struct.pack("!I", len(data))
        self._writer.write(size)
        self._writer.write(data)
        await self._writer.drain()

    async def _receive(self) -> Optional[bytes]:
        assert self._reader is not None
        try:
            self.logger.debug("Waiting for messages...")
            buf = await self._reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
            data = await self._reader.readexactly(size)
            if not data:  # pragma: no cover
                return None
            return data
        except asyncio.streams.IncompleteReadError as e:
            self.logger.info(
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None

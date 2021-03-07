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
from asyncio import CancelledError
from contextlib import suppress
from pathlib import Path
from typing import Any, List, Optional, Union, cast

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.registries import make_crypto
from aea.exceptions import enforce
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.acn.uri import Uri
from aea.mail.base import Envelope

from packages.fetchai.connections.p2p_libp2p_client.acn_message_pb2 import AcnMessage
from packages.fetchai.connections.p2p_libp2p_client.acn_message_pb2 import (
    AgentRecord as AgentRecordPb,
)
from packages.fetchai.connections.p2p_libp2p_client.acn_message_pb2 import (
    Register,
    Status,
)


try:
    from asyncio.streams import IncompleteReadError  # pylint: disable=ungrouped-imports
except ImportError:  # pragma: nocover
    from asyncio import IncompleteReadError  # pylint: disable=ungrouped-imports


_default_logger = logging.getLogger(
    "aea.packages.fetchai.connections.p2p_libp2p_client"
)

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p_client:0.14.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

POR_DEFAULT_SERVICE_ID = "acn"

ACN_CURRENT_VERSION = "0.1.0"


class P2PLibp2pClientConnection(Connection):
    """
    A libp2p client connection.

    Send and receive envelopes to and from agents on the p2p network without deploying a libp2p node.
    Connect to the libp2p node using traffic delegation service.
    """

    connection_id = PUBLIC_ID

    DEFAULT_CONNECT_RETRIES = 3

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a libp2p client connection."""
        super().__init__(**kwargs)

        self.connect_retries = self.configuration.config.get(
            "connect_retries", self.DEFAULT_CONNECT_RETRIES
        )
        ledger_id = self.configuration.config.get("ledger_id", DEFAULT_LEDGER)
        if ledger_id not in SUPPORTED_LEDGER_IDS:
            raise ValueError(  # pragma: nocover
                "Ledger id '{}' is not supported. Supported ids: '{}'".format(
                    ledger_id, SUPPORTED_LEDGER_IDS
                )
            )

        key_file = self.configuration.config.get("client_key_file")  # Optional[str]
        nodes = self.configuration.config.get("nodes")

        if nodes is None:
            raise ValueError("At least one node should be provided")
        nodes = list(cast(List, nodes))

        nodes_uris = [node.get("uri", None) for node in nodes]
        enforce(
            len(nodes_uris) == len(nodes) and None not in nodes_uris,
            "Delegate 'uri' should be provided for each node",
        )

        nodes_public_keys = [node.get("public_key", None) for node in nodes]
        enforce(
            len(nodes_public_keys) == len(nodes) and None not in nodes_public_keys,
            "Delegate 'public_key' should be provided for each node",
        )

        cert_requests = self.configuration.cert_requests
        if cert_requests is None or len(cert_requests) != len(nodes):
            raise ValueError(  # pragma: nocover
                "cert_requests field must be set and contain exactly as many entries as 'nodes'!"
            )
        for cert_request in cert_requests:
            save_path = cert_request.get_absolute_save_path(Path(self.data_dir))
            if not save_path.is_file():
                raise Exception(  # pragma: nocover
                    "cert_request 'save_path' field is not a file. "
                    "Please ensure that 'issue-certificates' command is called beforehand"
                )

        # TOFIX(): we cannot use store as the key will be used for TLS tcp connection
        #   also, as of now all the connections share the same key
        if key_file is not None:
            key = make_crypto(ledger_id, private_key_path=key_file)
        else:
            key = make_crypto(ledger_id)

        # client connection id
        self.key = key
        self.logger.debug("Public key used by libp2p client: {}".format(key.public_key))

        # delegate uris
        self.delegate_uris = [Uri(node_uri) for node_uri in nodes_uris]

        # delegates PoRs
        self.delegate_pors: List[AgentRecord] = []
        for i, cert_request in enumerate(cert_requests):
            agent_record = AgentRecord.from_cert_request(
                cert_request, self.address, nodes_public_keys[i], self.data_dir
            )
            self.delegate_pors.append(agent_record)

        # select a delegate
        index = random.randint(0, len(self.delegate_uris) - 1)  # nosec
        self.node_uri = self.delegate_uris[index]
        self.node_por = self.delegate_pors[index]
        self.logger.debug("Node to use as delegate: {}".format(self.node_uri))

        # tcp connection
        self._reader = None  # type: Optional[asyncio.StreamReader]
        self._writer = None  # type: Optional[asyncio.StreamWriter]

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._process_messages_task = None  # type: Union[asyncio.Future, None]

    async def connect(self) -> None:
        """
        Set up the connection.

        :return: None
        """
        if self.is_connected:  # pragma: nocover
            return

        self.state = ConnectionStates.connecting

        try:
            # connect libp2p client

            await self._perform_connection_to_node()
            # start receiving msgs
            self._in_queue = asyncio.Queue()
            self._process_messages_task = asyncio.ensure_future(
                self._process_messages(), loop=self.loop
            )
            self.state = ConnectionStates.connected
        except (CancelledError, Exception):
            self.state = ConnectionStates.disconnected
            raise

    async def _perform_connection_to_node(self) -> None:
        """Connect to node with retries."""
        for attempt in range(self.connect_retries):
            if self.state not in [
                ConnectionStates.connecting,
                ConnectionStates.connected,
            ]:
                # do nothing if disconnected, or disconnecting
                return  # pragma: nocover
            try:
                self.logger.info(
                    "Connecting to libp2p node {}. Attempt {}".format(
                        str(self.node_uri), attempt + 1
                    )
                )

                # connect the tcp socket
                self._reader, self._writer = await asyncio.open_connection(
                    self.node_uri.host,
                    self.node_uri._port,  # pylint: disable=protected-access
                    loop=self.loop,
                )

                # send agent address to node
                await self._setup_connection()

                self.logger.info(
                    "Successfully connected to libp2p node {}".format(
                        str(self.node_uri)
                    )
                )
                return
            except Exception as e:  # pylint: disable=broad-except
                if attempt == self.connect_retries - 1:
                    self.logger.error(
                        "Connection to  libp2p node {} failed: error: {}. It was the last attempt, exception will be raised".format(
                            str(self.node_uri), str(e)
                        )
                    )
                    self.state = ConnectionStates.disconnected
                    raise
                sleep_time = attempt * 2 + 1
                self.logger.error(
                    "Connection to  libp2p node {} failed: error: {}. Another attempt will be performed in {} seconds".format(
                        str(self.node_uri), str(e), sleep_time
                    )
                )
                await asyncio.sleep(sleep_time)

    async def _setup_connection(self) -> None:
        """Set up connection to node over tcp connection."""
        record = AgentRecordPb()
        record.address = self.node_por.address
        record.public_key = self.node_por.public_key
        record.peer_public_key = self.node_por.representative_public_key
        record.signature = self.node_por.signature
        record.service_id = POR_DEFAULT_SERVICE_ID
        record.ledger_id = self.node_por.ledger_id

        registration = Register()
        registration.record.CopyFrom(record)  # pylint: disable=no-member
        msg = AcnMessage()
        msg.version = ACN_CURRENT_VERSION
        msg.register.CopyFrom(registration)  # pylint: disable=no-member

        buf = msg.SerializeToString()
        await self._send(buf)

        self.logger.debug("Waiting for registration message...")
        try:
            buf = await self._read_message_from_reader()
        except ConnectionError as e:  # pragma: nocover
            self.logger.error(f"Connection error: {e}.")
            raise e
        except IncompleteReadError as e:  # pragma: no cover
            self.logger.error(
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            raise e
        if buf is None:  # pragma: nocover
            raise ConnectionError(
                "Error on connection setup. Incoming buffer is empty!"
            )
        msg = AcnMessage()
        msg.ParseFromString(buf)
        payload = msg.WhichOneof("payload")
        if payload != "status":  # pragma: nocover
            raise Exception(f"Wrong response message from peer: {payload}")
        response = msg.status  # pylint: disable=no-member

        if response.code != Status.SUCCESS:  # type: ignore # pylint: disable=no-member
            raise Exception(  # pragma: nocover
                "Registration to peer failed: {}".format(
                    Status.ErrCode.Name(response.code)  # type: ignore # pylint: disable=no-member
                )
            )

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        if self.is_disconnected:  # pragma: nocover
            return

        if self._process_messages_task is None:
            raise ValueError("Message task is not set.")  # pragma: nocover

        if self._writer is None:
            raise ValueError("Writer is not set.")  # pragma: nocover

        self.state = ConnectionStates.disconnecting
        if self._process_messages_task is not None:
            self._process_messages_task.cancel()
            # TOFIX(LR) mypy issue https://github.com/python/mypy/issues/8546
            # self._process_messages_task = None # noqa: E800

        self.logger.debug("disconnecting libp2p client connection...")

        with suppress(Exception):
            # supress if writer closed already
            self._writer.write_eof()
            await self._writer.drain()
            self._writer.close()

        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:  # pragma: no cover
            self.logger.debug("Called disconnect when input queue not initialized.")
        self.state = ConnectionStates.disconnected

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover
            data = await self._in_queue.get()
            if data is None:  # pragma: no cover
                self.logger.debug("Received None.")
                return None
            self.logger.debug("Received data: {}".format(data))
            return Envelope.decode(data)
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: no cover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: Envelope) -> None:
        """
        Send messages.

        :return: None
        """
        self._ensure_valid_envelope_for_external_comms(envelope)
        try:
            await self._send(envelope.encode())
        except Exception:  # pylint: disable=broad-except
            self.logger.exception(
                "Exception raised on message send. Try reconnect and send again."
            )
            await self._perform_connection_to_node()
            await self._send(envelope.encode())

    async def _process_messages(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        while True:
            data = await self._receive()
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover
            self._in_queue.put_nowait(data)
            if data is None:
                break  # pragma: no cover

    async def _send(self, data: bytes) -> None:
        if self._writer is None:
            raise ValueError("Writer is not set.")  # pragma: nocover
        size = struct.pack("!I", len(data))
        self._writer.write(size)
        self._writer.write(data)
        await self._writer.drain()

    async def _read_message_from_reader(self) -> Optional[bytes]:
        """Try to read message from reader."""
        if self._reader is None:
            raise ValueError("Reader is not set.")  # pragma: nocover

        buf = await self._reader.readexactly(4)
        if not buf:  # pragma: no cover
            return None
        size = struct.unpack("!I", buf)[0]
        data = await self._reader.readexactly(size)
        if not data:  # pragma: no cover
            return None
        return data

    async def _receive(self) -> Optional[bytes]:
        """Receive binary message."""
        try:
            self.logger.debug("Waiting for messages...")
            return await self._read_message_from_reader()
        except ConnectionError as e:  # pragma: nocover
            self.logger.error(f"Connection error: {e}. Try to reconnect and read again")
        except IncompleteReadError as e:  # pragma: no cover
            self.logger.error(
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
        try:
            await self._perform_connection_to_node()
            return await self._read_message_from_reader()
        except Exception:  # pragma: no cover  # pylint: disable=broad-except
            self.logger.exception("Failed to read with reconnect!")
            return None

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
from asyncio import CancelledError
from pathlib import Path
from typing import Any, Dict, List, Optional

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.registries import make_crypto
from aea.exceptions import enforce
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.acn.uri import Uri
from aea.helpers.base import SimpleIdOrStr
from aea.helpers.pipe import IPCChannelClient, TCPSocketChannelClient
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

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p_client:0.18.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

POR_DEFAULT_SERVICE_ID = "acn"

ACN_CURRENT_VERSION = "0.1.0"


class NodeClient:
    """Client to communicate with node using ipc channel(pipe)."""

    def __init__(self, pipe: IPCChannelClient) -> None:
        """Set node client with pipe."""
        self.pipe = pipe

    async def connect(self) -> bool:
        """Connect to node with pipe."""
        return await self.pipe.connect()

    async def send_envelope(self, envelope: Envelope) -> None:
        """Send envelope to node."""
        await self._write(envelope.encode())

    async def read_envelope(self) -> Optional[Envelope]:
        """Read envelope from the node."""
        data = await self._read()

        if not data:
            return None

        return Envelope.decode(data)

    async def _write(self, data: bytes) -> None:
        """
        Write to the writer stream.

        :param data: data to write to stream
        """
        await self.pipe.write(data)

    async def _read(self) -> Optional[bytes]:
        """
        Read from the reader stream.

        :return: bytes
        """
        return await self.pipe.read()

    async def register(
        self,
        address: str,
        public_key: str,
        peer_public_key: str,
        signature: str,
        service_id: SimpleIdOrStr,
        ledger_id: SimpleIdOrStr,
    ) -> None:
        """Register agent on the remote node."""
        record = AgentRecordPb()
        record.address = address
        record.public_key = public_key
        record.peer_public_key = peer_public_key
        record.signature = signature
        record.service_id = service_id
        record.ledger_id = ledger_id

        registration = Register()
        registration.record.CopyFrom(record)  # pylint: disable=no-member
        msg = AcnMessage()
        msg.version = ACN_CURRENT_VERSION
        msg.register.CopyFrom(registration)  # pylint: disable=no-member

        buf = msg.SerializeToString()
        await self._write(buf)

        try:
            buf = await self._read()
        except ConnectionError as e:  # pragma: nocover
            raise e
        except IncompleteReadError as e:  # pragma: no cover
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

    async def close(self) -> None:
        """Close client and pipe."""
        await self.pipe.close()


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

        key_file: Optional[str] = self.configuration.config.get("tcp_key_file")
        nodes: Optional[List[Dict[str, Any]]] = self.configuration.config.get("nodes")

        if nodes is None:
            raise ValueError("At least one node should be provided")
        nodes = list(nodes)

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

        # we cannot use the key from the connection's crypto store as
        # the key will be used for TLS tcp connection, whereas the
        # connection's crypto store key is used for PoR
        if key_file is not None:
            key = make_crypto(ledger_id, private_key_path=key_file)
        else:
            key = make_crypto(ledger_id)

        # client connection id
        self.key = key
        self.logger.debug("Public key used for TCP: {}".format(key.public_key))

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
        self._process_messages_task = None  # type: Optional[asyncio.Future]
        self._node_client: Optional[NodeClient] = None

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
                pipe = TCPSocketChannelClient(
                    f"{self.node_uri.host}:{self.node_uri._port}",  # pylint: disable=protected-access
                    "",
                )
                await pipe.connect()
                self._node_client = NodeClient(pipe)
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
        if not self._node_client:  # pragma: nocover
            raise ValueError("Connection was not connected!")

        await self._node_client.register(
            address=self.node_por.address,
            public_key=self.node_por.public_key,
            peer_public_key=self.node_por.representative_public_key,
            signature=self.node_por.signature,
            service_id=POR_DEFAULT_SERVICE_ID,
            ledger_id=self.node_por.ledger_id,
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

        self.state = ConnectionStates.disconnecting
        if self._process_messages_task is not None:
            self._process_messages_task.cancel()
            self._process_messages_task = None

        self.logger.debug("disconnecting libp2p client connection...")

        if self._node_client is not None:
            await self._node_client.close()

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
            envelope = await self._in_queue.get()
            if envelope is None:  # pragma: no cover
                self.logger.debug("Received None.")
                return None
            self.logger.debug("Received envelope: {}".format(envelope))
            return envelope
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
        if not self._node_client:  # pragma: nocover
            raise ValueError("Connection not connected to node!")

        self._ensure_valid_envelope_for_external_comms(envelope)
        try:
            await self._node_client.send_envelope(envelope)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception(
                "Exception raised on message send. Try reconnect and send again."
            )
            await self._perform_connection_to_node()
            await self._node_client.send_envelope(envelope)

    async def _read_envelope_from_node(self) -> Optional[Envelope]:
        """Read envelope from node, reconnec on error."""
        if not self._node_client:  # pragma: nocover
            raise ValueError("Connection not connected to node!")

        try:
            self.logger.debug("Waiting for messages...")
            envelope = await self._node_client.read_envelope()
            return envelope
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
            envelope = await self._node_client.read_envelope()
            return envelope
        except Exception:  # pragma: no cover  # pylint: disable=broad-except
            self.logger.exception("Failed to read with reconnect!")
            return None

    async def _process_messages(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        if not self._node_client:  # pragma: nocover
            raise ValueError("Connection not connected to node!")

        while True:
            envelope = await self._read_envelope_from_node()
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover
            self._in_queue.put_nowait(envelope)
            if envelope is None:
                break  # pragma: no cover

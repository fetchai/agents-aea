# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
import contextlib
import hashlib
import logging
import random
import ssl
from asyncio import CancelledError
from asyncio.events import AbstractEventLoop
from asyncio.streams import StreamWriter
from pathlib import Path
from typing import Any, Dict, List, Optional

from asn1crypto import x509  # type: ignore
from ecdsa.curves import SECP256k1
from ecdsa.keys import BadSignatureError, VerifyingKey
from ecdsa.util import sigdecode_der

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.registries import make_crypto
from aea.exceptions import enforce
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.acn.uri import Uri
from aea.helpers.pipe import IPCChannelClient, TCPSocketChannelClient, TCPSocketProtocol
from aea.mail.base import Envelope

from packages.valory.protocols.acn import acn_pb2
from packages.valory.protocols.acn.message import AcnMessage


try:
    from asyncio.streams import IncompleteReadError  # pylint: disable=ungrouped-imports
except ImportError:  # pragma: nocover
    from asyncio import IncompleteReadError  # pylint: disable=ungrouped-imports


_default_logger = logging.getLogger("aea.packages.valory.connections.p2p_libp2p_client")

PUBLIC_ID = PublicId.from_str("valory/p2p_libp2p_client:0.1.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

POR_DEFAULT_SERVICE_ID = "acn"

ACN_CURRENT_VERSION = "0.1.0"


class NodeClient:
    """Client to communicate with node using ipc channel(pipe)."""

    ACN_ACK_TIMEOUT = 5.0

    def __init__(self, pipe: IPCChannelClient, node_por: AgentRecord) -> None:
        """Set node client with pipe."""
        self.pipe = pipe
        self._wait_status: Optional[asyncio.Future] = None
        self.agent_record = node_por

    async def wait_for_status(self) -> Any:
        """Get status."""
        if self._wait_status is None:  # pragma: nocover
            raise ValueError("waiter for status not set!")
        return await asyncio.wait_for(self._wait_status, timeout=self.ACN_ACK_TIMEOUT)

    @staticmethod
    def make_acn_envelope_message(envelope: Envelope) -> bytes:
        """Make acn message with envelope in."""
        acn_msg = acn_pb2.AcnMessage()
        performative = acn_pb2.AcnMessage.Aea_Envelope_Performative()  # type: ignore
        performative.envelope = envelope.encode()
        acn_msg.aea_envelope.CopyFrom(performative)  # pylint: disable=no-member
        buf = acn_msg.SerializeToString()
        return buf

    async def write_acn_status_ok(self) -> None:
        """Send acn status ok."""
        acn_msg = acn_pb2.AcnMessage()
        performative = acn_pb2.AcnMessage.Status_Performative()  # type: ignore
        status = AcnMessage.StatusBody(
            status_code=AcnMessage.StatusBody.StatusCode.SUCCESS, msgs=[]
        )
        AcnMessage.StatusBody.encode(
            performative.body, status  # pylint: disable=no-member
        )
        acn_msg.status.CopyFrom(performative)  # pylint: disable=no-member
        buf = acn_msg.SerializeToString()
        await self._write(buf)

    async def write_acn_status_error(
        self,
        msg: str,
        status_code: AcnMessage.StatusBody.StatusCode = AcnMessage.StatusBody.StatusCode.ERROR_GENERIC,  # type: ignore
    ) -> None:
        """Send acn status error generic."""
        acn_msg = acn_pb2.AcnMessage()
        performative = acn_pb2.AcnMessage.Status_Performative()  # type: ignore
        status = AcnMessage.StatusBody(status_code=status_code, msgs=[msg])
        AcnMessage.StatusBody.encode(
            performative.body, status  # pylint: disable=no-member
        )
        acn_msg.status.CopyFrom(performative)  # pylint: disable=no-member

        buf = acn_msg.SerializeToString()

        await self._write(buf)

    async def connect(self) -> bool:
        """Connect to node with pipe."""
        return await self.pipe.connect()

    async def send_envelope(self, envelope: Envelope) -> None:
        """Send envelope to node."""
        self._wait_status = asyncio.Future()
        buf = self.make_acn_envelope_message(envelope)
        await self._write(buf)
        try:
            status = await self.wait_for_status()
            if status.code != int(AcnMessage.StatusBody.StatusCode.SUCCESS):  # type: ignore  # pylint: disable=no-member
                raise ValueError(  # pragma: nocover
                    f"failed to send envelope. got error confirmation: {status}"
                )
        except asyncio.TimeoutError:  # pragma: nocover
            if not self._wait_status.done():  # pragma: nocover
                self._wait_status.set_exception(Exception("Timeout"))
            await asyncio.sleep(0)
            raise ValueError("acn status await timeout!")
        finally:
            self._wait_status = None

    def make_agent_record(self) -> AcnMessage.AgentRecord:  # type: ignore
        """Make acn agent record."""
        agent_record = AcnMessage.AgentRecord(
            address=self.agent_record.address,
            public_key=self.agent_record.public_key,
            peer_public_key=self.agent_record.representative_public_key,
            signature=self.agent_record.signature,
            service_id=POR_DEFAULT_SERVICE_ID,
            ledger_id=self.agent_record.ledger_id,
        )
        return agent_record

    async def read_envelope(self) -> Optional[Envelope]:
        """Read envelope from the node."""
        while True:
            buf = await self._read()

            if not buf:
                return None

            try:
                acn_msg = acn_pb2.AcnMessage()
                acn_msg.ParseFromString(buf)

            except Exception as e:  # pragma: nocover
                await self.write_acn_status_error(
                    f"Failed to parse acn message {e}",
                    status_code=AcnMessage.StatusBody.StatusCode.ERROR_DECODE,
                )
                raise ValueError(f"Error parsing acn message: {e}") from e

            performative = acn_msg.WhichOneof("performative")
            if performative == "aea_envelope":  # pragma: nocover
                aea_envelope = acn_msg.aea_envelope  # pylint: disable=no-member
                try:
                    envelope = Envelope.decode(aea_envelope.envelope)
                    await self.write_acn_status_ok()
                    return envelope
                except Exception as e:
                    await self.write_acn_status_error(
                        f"Failed to decode envelope: {e}",
                        status_code=AcnMessage.StatusBody.StatusCode.ERROR_DECODE,
                    )
                    raise

            elif performative == "status":
                if self._wait_status is not None:
                    self._wait_status.set_result(
                        acn_msg.status.body  # pylint: disable=no-member
                    )
            else:  # pragma: nocover
                await self.write_acn_status_error(
                    f"Bad acn message {performative}",
                    status_code=AcnMessage.StatusBody.StatusCode.ERROR_UNEXPECTED_PAYLOAD,
                )

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
    ) -> None:
        """Register agent on the remote node."""
        agent_record = self.make_agent_record()
        acn_msg = acn_pb2.AcnMessage()
        performative = acn_pb2.AcnMessage.Register_Performative()  # type: ignore
        AcnMessage.AgentRecord.encode(
            performative.record, agent_record  # pylint: disable=no-member
        )
        acn_msg.register.CopyFrom(performative)  # pylint: disable=no-member

        buf = acn_msg.SerializeToString()
        await self._write(buf)

        try:
            buf = await asyncio.wait_for(self._read(), timeout=self.ACN_ACK_TIMEOUT)
        except ConnectionError as e:  # pragma: nocover
            raise e
        except IncompleteReadError as e:  # pragma: no cover
            raise e

        if buf is None:  # pragma: nocover
            raise ConnectionError(
                "Error on connection setup. Incoming buffer is empty!"
            )
        acn_msg = acn_pb2.AcnMessage()
        acn_msg.ParseFromString(buf)
        performative = acn_msg.WhichOneof("performative")
        if performative != "status":  # pragma: nocover
            raise Exception(f"Wrong response message from peer: {performative}")
        response = acn_msg.status  # pylint: disable=no-member

        if response.body.code != int(AcnMessage.StatusBody.StatusCode.SUCCESS):  # type: ignore # pylint: disable=no-member
            raise Exception(  # pragma: nocover
                "Registration to peer failed: {}".format(
                    AcnMessage.StatusBody.StatusCode(response.body.code)  # type: ignore # pylint: disable=no-member
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
    DEFAULT_TLS_CONNECTION_SIGNATURE_TIMEOUT = 5.0

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a libp2p client connection."""
        super().__init__(**kwargs)

        self.tls_connection_signature_timeout = self.configuration.config.get(
            "tls_connection_signature_timeout",
            self.DEFAULT_TLS_CONNECTION_SIGNATURE_TIMEOUT,
        )
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

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._process_messages_task = None  # type: Optional[asyncio.Future]
        self._node_client: Optional[NodeClient] = None

        self._send_queue: Optional[asyncio.Queue] = None
        self._send_task: Optional[asyncio.Task] = None

    async def _send_loop(self) -> None:
        """Handle message in  the send queue."""

        if not self._send_queue or not self._node_client:  # pragma: nocover
            self.logger.error("Send loop not started cause not connected properly.")
            return
        try:
            while self.is_connected:
                envelope = await self._send_queue.get()
                await self._send_envelope_with_node_client(envelope)
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise  # pragma: nocover
        except Exception:  # pylint: disable=broad-except # pragma: nocover
            self.logger.exception(
                f"Failed to send an envelope {envelope}. Stop connection."
            )
            await asyncio.shield(self.disconnect())

    async def _send_envelope_with_node_client(self, envelope: Envelope) -> None:
        """Send envelope with node client, reconnect and retry on fail."""
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

    async def connect(self) -> None:
        """Set up the connection."""
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            # connect libp2p client

            await self._perform_connection_to_node()
            # start receiving msgs
            self._in_queue = asyncio.Queue()
            self._process_messages_task = asyncio.ensure_future(
                self._process_messages(), loop=self.loop
            )
            self._send_queue = asyncio.Queue()
            self._send_task = self.loop.create_task(self._send_loop())

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
                pipe = TCPSocketChannelClientTLS(
                    f"{self.node_uri.host}:{self.node_uri._port}",  # pylint: disable=protected-access
                    "",
                    server_pub_key=self.node_por.representative_public_key,
                    verification_signature_wait_timeout=self.tls_connection_signature_timeout,
                )
                if not await pipe.connect():
                    raise ValueError(
                        f"Pipe connection error: {pipe.last_exception or ''}"
                    ) from pipe.last_exception

                self._node_client = NodeClient(pipe, self.node_por)
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

        await self._node_client.register()

    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting
        self.logger.debug("disconnecting libp2p client connection...")

        if self._process_messages_task is not None:
            if not self._process_messages_task.done():
                self._process_messages_task.cancel()
            self._process_messages_task = None

        if self._send_task is not None:
            if not self._send_task.done():
                self._send_task.cancel()
            self._send_task = None

        try:
            self.logger.debug("disconnecting libp2p node client connection...")
            if self._node_client is not None:
                await self._node_client.close()
        except Exception:  # pragma: nocover  # pylint:disable=broad-except
            self.logger.exception("exception on node client close")
            raise
        finally:
            # set disconnected state anyway
            if self._in_queue is not None:
                self._in_queue.put_nowait(None)

            self.state = ConnectionStates.disconnected
            self.logger.debug("libp2p client connection disconnected.")

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :param args: positional arguments
        :param kwargs: keyword arguments
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

        :param envelope: the envelope
        """
        if not self._node_client or not self._send_queue:
            raise ValueError("Node is not connected!")  # pragma: nocover

        self._ensure_valid_envelope_for_external_comms(envelope)
        await self._send_queue.put(envelope)

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
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            self.logger.exception(f"On envelope read: {e}")

        try:
            self.logger.debug("Read envelope retry! Reconnect first!")
            await self._perform_connection_to_node()
            envelope = await self._node_client.read_envelope()
            return envelope
        except Exception:  # pragma: no cover  # pylint: disable=broad-except
            self.logger.exception("Failed to read with reconnect!")
            return None

    async def _process_messages(self) -> None:
        """Receive data from node."""
        if not self._node_client:  # pragma: nocover
            raise ValueError("Connection not connected to node!")

        while True:
            envelope = await self._read_envelope_from_node()
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover
            self._in_queue.put_nowait(envelope)
            if envelope is None:
                break  # pragma: no cover


class TCPSocketChannelClientTLS(TCPSocketChannelClient):
    """Interprocess communication channel client using tcp sockets with TLS."""

    DEFAULT_VERIFICATION_SIGNATURE_WAIT_TIMEOUT = 5.0

    def __init__(
        self,
        in_path: str,
        out_path: str,
        server_pub_key: str,
        logger: logging.Logger = _default_logger,
        loop: Optional[AbstractEventLoop] = None,
        verification_signature_wait_timeout: Optional[float] = None,
    ) -> None:
        """
        Initialize a tcp socket communication channel client.

        :param in_path: rendezvous point for incoming data
        :param out_path: rendezvous point for outgoing data
        :param server_pub_key: str, server public key to verify identity
        :param logger: the logger
        :param loop: the event loop
        :param verification_signature_wait_timeout: optional float, if not provided, default value will be used
        """
        super().__init__(in_path, out_path, logger, loop)
        self.verification_signature_wait_timeout = (
            self.DEFAULT_VERIFICATION_SIGNATURE_WAIT_TIMEOUT
            if verification_signature_wait_timeout is None
            else verification_signature_wait_timeout
        )
        self.server_pub_key = server_pub_key

    @staticmethod
    def _get_session_pub_key(writer: StreamWriter) -> bytes:  # pragma: nocover
        """Get session public key from tls stream writer."""
        cert_data = writer.get_extra_info("ssl_object").getpeercert(binary_form=True)

        cert = x509.Certificate.load(cert_data)
        session_pub_key = VerifyingKey.from_der(cert.public_key.dump()).to_string(
            "uncompressed"
        )
        return session_pub_key

    async def _open_connection(self) -> TCPSocketProtocol:
        """Open a connection with TLS support and verify peer."""
        sock = await self._open_tls_connection()
        session_pub_key = self._get_session_pub_key(sock.writer)

        try:
            signature = await asyncio.wait_for(
                sock.read(), timeout=self.verification_signature_wait_timeout
            )
        except asyncio.TimeoutError:  # pragma: nocover
            raise ValueError(
                f"Failed to get peer verification record in timeout: {self.verification_signature_wait_timeout}"
            )

        if not signature:  # pragma: nocover
            raise ValueError("Unexpected socket read data!")

        try:
            self._verify_session_key_signature(signature, session_pub_key)
        except BadSignatureError as e:  # pragma: nocover
            with contextlib.suppress(Exception):
                await sock.close()
            raise ValueError(f"Invalid TLS session key signature: {e}")
        return sock

    async def _open_tls_connection(self) -> TCPSocketProtocol:
        """Open a connection with TLS support."""
        cadata = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ssl.get_server_certificate((self._host, self._port))
        )

        ssl_ctx = ssl.create_default_context(cadata=cadata)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        reader, writer = await asyncio.open_connection(
            self._host,
            self._port,
            ssl=ssl_ctx,
        )
        return TCPSocketProtocol(reader, writer, logger=self.logger, loop=self._loop)

    def _verify_session_key_signature(
        self, signature: bytes, session_pub_key: bytes
    ) -> None:
        """
        Validate signature of session public key.

        :param signature: bytes, signature of session public key made with server private key
        :param session_pub_key: session public key to check signature for.
        """
        vk = VerifyingKey.from_string(bytes.fromhex(self.server_pub_key), SECP256k1)
        vk.verify(
            signature, session_pub_key, hashfunc=hashlib.sha256, sigdecode=sigdecode_der
        )

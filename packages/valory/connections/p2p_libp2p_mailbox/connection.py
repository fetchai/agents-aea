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
import hashlib
import logging
import random
import re
import ssl
from asyncio import CancelledError
from asyncio.streams import StreamWriter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

import aiohttp
from aiohttp.client_reqrep import ClientResponse
from asn1crypto import x509  # type: ignore
from ecdsa.curves import SECP256k1
from ecdsa.keys import VerifyingKey
from ecdsa.util import sigdecode_der

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.registries import make_crypto
from aea.exceptions import enforce
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.acn.uri import Uri
from aea.mail.base import Envelope

from packages.valory.protocols.acn import acn_pb2
from packages.valory.protocols.acn.message import AcnMessage


try:
    from asyncio.streams import IncompleteReadError  # pylint: disable=ungrouped-imports
except ImportError:  # pragma: nocover
    from asyncio import IncompleteReadError  # pylint: disable=ungrouped-imports


_default_logger = logging.getLogger("aea.packages.valory.connections.p2p_libp2p_client")

PUBLIC_ID = PublicId.from_str("valory/p2p_libp2p_mailbox:0.1.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

POR_DEFAULT_SERVICE_ID = "acn"

ACN_CURRENT_VERSION = "0.1.0"


class NodeClient:
    """Client to communicate with node using ipc channel(pipe)."""

    NO_ENVELOPES_SLEEP_TIME: float = 2.0

    def __init__(self, node_uri: Uri, node_por: AgentRecord) -> None:
        """Set node client with pipe."""
        self.node_uri = node_uri
        self.agent_record = node_por
        self._session_token: Optional[str] = None
        self.ssl_ctx = Optional[ssl.SSLContext]

    async def connect(self) -> bool:
        """Connect to node with pipe."""
        url = f"https://{self.node_uri}/ssl_signature"
        self.ssl_ctx = await SSLValidator(
            url, self.agent_record.representative_public_key
        ).check()
        await self.register()
        return True

    async def send_envelope(self, envelope: Envelope) -> None:
        """Send envelope to node."""
        if not self._session_token:  # pragma: nocover
            raise ValueError("not connected!")

        envelope_data = envelope.encode()
        # send here
        response, _ = await self._perform_http_request(
            method="POST",
            url="/send_envelope",
            data=envelope_data,
            headers={"Session-Id": self._session_token},
        )

        if response.status != 200:  # pragma: nocover
            text = await response.text()
            raise ValueError(f"Bad response code: {response.status} {text}")

    async def _perform_http_request(
        self, method: str, url: str, **kwargs: Any
    ) -> Tuple[ClientResponse, bytes]:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url=f"https://{self.node_uri}{url}", ssl=self.ssl_ctx, **kwargs
            ) as response:
                data = await response.read()
                return response, data

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
        """Read envelope from the mailbox node."""
        while True:
            if not self._session_token:  # pragma: nocover
                raise ValueError("Client not registered!")
            response, data = await self._perform_http_request(
                "GET", "/get_envelope", headers={"Session-Id": self._session_token}
            )
            if response.status != 200:  # pragma: nocover
                raise ValueError(f"Bad response code: {response.status}")

            if not data:
                await asyncio.sleep(self.NO_ENVELOPES_SLEEP_TIME)
                continue

            envelope = Envelope.decode(data)
            return envelope

    async def register(self) -> None:
        """Register agent on the remote node."""
        agent_record = self.make_agent_record()
        performative = acn_pb2.AcnMessage.Register_Performative()  # type: ignore
        AcnMessage.AgentRecord.encode(
            performative.record, agent_record  # pylint: disable=no-member
        )
        data = performative.record.SerializeToString()  # pylint: disable=no-member
        response, _ = await self._perform_http_request(
            "POST", url="/register", data=data
        )

        if response.status != 200:  # pragma: nocover
            raise ValueError(f"Bad response code: {response.status}")

        token = await response.text()
        if not re.match("[0-9a-f]{32}", token, re.I):  # pragma: nocover
            raise ValueError(f"invalid response: {token}")

        self._session_token = token

    async def close(self) -> None:
        """Close node connection."""
        if not self._session_token:  # pragma: nocover
            raise ValueError("not connected!")

        response, _ = await self._perform_http_request(
            "GET", "/unregister", headers={"Session-Id": self._session_token}
        )
        if response.status != 200:  # pragma: nocover
            raise ValueError(f"Bad response code: {response.status}")

        self._session_token = None


class P2PLibp2pMailboxConnection(Connection):
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
                self._node_client = NodeClient(self.node_uri, self.node_por)
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

        await self._node_client.connect()

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
            return envelope  # pragma: no cover
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


class SSLValidator:
    """Interprocess communication channel client using tcp sockets with TLS."""

    def __init__(
        self,
        url: str,
        server_pub_key: str,
        logger: logging.Logger = _default_logger,
    ) -> None:
        """
        Check ssl certificate with server pub key.

        :param url: url to get signature
        :param server_pub_key: str, server public key to verify identity
        :param logger: the logger
        """
        self.server_pub_key = server_pub_key
        o = urlparse(url)
        self.url = url
        self.logger = logger
        self.host: str = cast(str, o.hostname)
        self.port: int = cast(int, o.port)

    async def check(self) -> ssl.SSLContext:
        """Check ssl/pubkey for mailbox service and return ssl context."""
        ssl_ctx, session_pub_key = await self.get_ssl_ctx_and_session_pub_key(
            self.host, self.port
        )
        signature = await self.get_signature(ssl_ctx)
        self._verify_session_key_signature(
            self.server_pub_key, signature, session_pub_key
        )
        return ssl_ctx

    async def get_signature(self, ssl_ctx: ssl.SSLContext) -> bytes:
        """
        Get signature for mailbox service (ssl pubkey signed with node private key).

        :param ssl_ctx: ssl context.

        :return: signature in bytes
        """
        async with aiohttp.ClientSession() as client:
            async with client.get(self.url, ssl=ssl_ctx) as resp:
                if resp.status != 200:  # pragma: nocover
                    raise ValueError("Bad server response")
                signature = await resp.read()
        return signature

    @staticmethod
    def _get_session_pub_key(writer: StreamWriter) -> bytes:  # pragma: nocover
        """Get session public key from tls stream writer."""
        cert_data = writer.get_extra_info("ssl_object").getpeercert(binary_form=True)

        cert = x509.Certificate.load(cert_data)
        session_pub_key = VerifyingKey.from_der(cert.public_key.dump()).to_string(
            "uncompressed"
        )
        return session_pub_key

    async def get_ssl_ctx_and_session_pub_key(
        self, host: str, port: int
    ) -> Tuple[ssl.SSLContext, bytes]:
        """Open a connection with TLS support."""
        cadata = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ssl.get_server_certificate((host, port))
        )

        ssl_ctx = ssl.create_default_context(cadata=cadata)
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        _, writer = await asyncio.open_connection(
            self.host,
            self.port,
            ssl=ssl_ctx,
        )
        session_pub_key = self._get_session_pub_key(writer)
        writer.close()
        return ssl_ctx, session_pub_key

    @staticmethod
    def _verify_session_key_signature(
        server_pub_key: str, signature: bytes, session_pub_key: bytes
    ) -> None:
        """
        Validate signature of session public key.

        :param server_pub_key: node pub key/addr.
        :param signature: bytes, signature of session public key made with server private key
        :param session_pub_key: session public key to check signature for.
        """
        vk = VerifyingKey.from_string(bytes.fromhex(server_pub_key), SECP256k1)
        vk.verify(
            signature, session_pub_key, hashfunc=hashlib.sha256, sigdecode=sigdecode_der
        )

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
"""This module contains the p2p libp2p connection."""
import asyncio
import logging
import os
import platform
import subprocess  # nosec
import sys
from asyncio import AbstractEventLoop, CancelledError, events
from ipaddress import ip_address
from pathlib import Path
from socket import gethostbyname
from typing import Any, IO, List, Optional, Sequence, cast

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.base import Crypto
from aea.exceptions import enforce
from aea.helpers.acn.agent_record import AgentRecord
from aea.helpers.acn.uri import Uri
from aea.helpers.multiaddr.base import MultiAddr
from aea.helpers.pipe import IPCChannel, TCPSocketChannel
from aea.mail.base import Envelope

from packages.valory.connections.p2p_libp2p.consts import LIBP2P_NODE_MODULE_NAME
from packages.valory.protocols.acn import acn_pb2
from packages.valory.protocols.acn.message import AcnMessage


_default_logger = logging.getLogger("aea.packages.valory.connections.p2p_libp2p")

ACN_CURRENT_VERSION = "0.1.0"

LIBP2P_NODE_LOG_FILE = "libp2p_node.log"

LIBP2P_NODE_ENV_FILE = ".env.libp2p"

LIBP2P_NODE_CLARGS = list()  # type: List[str]


PIPE_CONN_TIMEOUT = 10.0

PUBLIC_ID = PublicId.from_str("valory/p2p_libp2p:0.1.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

LIBP2P_SUCCESS_MESSAGE = "Peer running in "

POR_DEFAULT_SERVICE_ID = "acn"


def _ip_all_private_or_all_public(addrs: List[str]) -> bool:
    if len(addrs) == 0:
        return True

    is_private = ip_address(gethostbyname(addrs[0])).is_private
    is_loopback = ip_address(gethostbyname(addrs[0])).is_loopback

    for addr in addrs:
        if ip_address(gethostbyname(addr)).is_private != is_private:
            return False  # pragma: nocover
        if ip_address(gethostbyname(addr)).is_loopback != is_loopback:
            return False
    return True


def _golang_module_run(
    path: str,
    name: str,
    args: Sequence[str],
    log_file_desc: IO[str],
    logger: logging.Logger = _default_logger,
) -> subprocess.Popen:
    """
    Runs a built module located at `path`.

    :param path: the path to the go module.
    :param name: the name of the module.
    :param args: the args
    :param log_file_desc: the file descriptor of the log file.
    :param logger: the logger
    :return: subprocess
    """
    cmd = [os.path.join(path, name)]

    cmd.extend(args)

    env = os.environ
    try:
        logger.debug(cmd)
        proc = subprocess.Popen(  # nosec
            cmd,
            cwd=path,
            env=env,
            stdout=log_file_desc,
            stderr=log_file_desc,
            shell=False,
        )
    except Exception as e:
        logger.error(
            "While executing go run . {} at {} : {}".format(path, args, str(e))
        )
        raise e

    return proc


class NodeClient:
    """Client to communicate with node using ipc channel(pipe)."""

    ACN_ACK_TIMEOUT = 5

    def __init__(self, pipe: IPCChannel, agent_record: AgentRecord) -> None:
        """Set node client with pipe."""
        self.pipe = pipe
        self.agent_record = agent_record
        self._wait_status: Optional[asyncio.Future] = None

    async def connect(self) -> bool:
        """Connect to node with pipe."""
        return await self.pipe.connect()

    async def send_envelope(self, envelope: Envelope) -> None:
        """Send envelope to node."""
        self._wait_status = asyncio.Future()
        buf = self.make_acn_envelope_message(envelope)
        await self._write(buf)

        status = await self.wait_for_status()

        if status.code != int(AcnMessage.StatusBody.StatusCode.SUCCESS):  # type: ignore  # pylint: disable=no-member
            raise ValueError(  # pragma: nocover
                f"failed to send envelope. got error confirmation: {status.code}"
            )

    async def wait_for_status(self) -> Any:
        """Get status."""
        if self._wait_status is None:  # pragma: nocover
            raise ValueError("value failed!")
        try:
            status = await asyncio.wait_for(
                self._wait_status, timeout=self.ACN_ACK_TIMEOUT
            )
            return status
        except asyncio.TimeoutError:  # pragma: nocover
            if not self._wait_status.done():  # pragma: nocover
                self._wait_status.set_exception(Exception("Timeout"))
            await asyncio.sleep(0)
            raise ValueError("acn status await timeout!")
        finally:
            self._wait_status = None

    @staticmethod
    def make_acn_envelope_message(envelope: Envelope) -> bytes:
        """Make acn message with envelope in."""
        acn_msg = acn_pb2.AcnMessage()
        performative = acn_pb2.AcnMessage.Aea_Envelope_Performative()  # type: ignore
        performative.envelope = envelope.encode()
        acn_msg.aea_envelope.CopyFrom(performative)  # pylint: disable=no-member
        buf = acn_msg.SerializeToString()
        return buf

    async def read_envelope(self) -> Optional[Envelope]:
        """Read envelope from the node."""
        while True:
            buf = await self._read()

            if not buf:
                return None

            try:
                acn_msg = acn_pb2.AcnMessage()
                acn_msg.ParseFromString(buf)

            except Exception as e:
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


class Libp2pNode:
    """Libp2p p2p node as a subprocess with named pipes interface."""

    def __init__(
        self,
        agent_record: AgentRecord,
        key: Crypto,
        module_path: str,
        data_dir: str,
        clargs: Optional[List[str]] = None,
        uri: Optional[Uri] = None,
        public_uri: Optional[Uri] = None,
        delegate_uri: Optional[Uri] = None,
        monitoring_uri: Optional[Uri] = None,
        entry_peers: Optional[Sequence[MultiAddr]] = None,
        log_file: Optional[str] = None,
        env_file: Optional[str] = None,
        logger: logging.Logger = _default_logger,
        peer_registration_delay: Optional[float] = None,
        records_storage_path: Optional[str] = None,
        connection_timeout: Optional[float] = None,
        max_restarts: int = 5,
        mailbox_uri: str = "127.0.0.1:8888",
    ):
        """
        Initialize a p2p libp2p node.

        :param agent_record: the agent proof-of-representation for peer.
        :param key: secp256k1 curve private key.
        :param module_path: the module path.
        :param data_dir: the data directory.
        :param clargs: the command line arguments for the libp2p node
        :param uri: libp2p node ip address and port number in format ipaddress:port.
        :param public_uri: libp2p node public ip address and port number in format ipaddress:port.
        :param delegate_uri: libp2p node delegate service ip address and port number in format ipaddress:port.
        :param monitoring_uri: libp2 node monitoring ip address and port in format ipaddress:port
        :param entry_peers: libp2p entry peers multiaddresses.
        :param log_file: the logfile path for the libp2p node
        :param env_file: the env file path for the exchange of environment variables
        :param logger: the logger.
        :param peer_registration_delay: add artificial delay to agent registration in seconds
        :param records_storage_path: the path where to store the agent records.
        :param connection_timeout: the connection timeout of the node.
        :param max_restarts: amount of node restarts during operation.
        :param mailbox_uri: libp2p mailbox_uri ip address and port number in format ipaddress:port.
        """

        self.record = agent_record
        self.address = self.record.address

        # node id in the p2p network
        self.key = key.private_key
        self.pub = key.public_key

        # node uri
        self.uri = uri if uri is not None else Uri()

        # node public uri, optional
        self.public_uri = public_uri

        # node delegate uri, optional
        self.delegate_uri = delegate_uri

        # node monitoring uri, optional
        self.monitoring_uri = monitoring_uri

        # entry peer
        self.entry_peers = entry_peers or []

        self.mailbox_uri = mailbox_uri

        # peer configuration
        self.peer_registration_delay = peer_registration_delay
        self.records_storage_path = records_storage_path
        if (
            self.records_storage_path is not None
            and not Path(self.records_storage_path).is_absolute()
        ):
            self.records_storage_path = os.path.join(  # pragma: nocover
                data_dir, self.records_storage_path
            )

        # node startup
        self.source = os.path.abspath(module_path)
        self.clargs = clargs or []

        # node libp2p multiaddress
        self.multiaddrs: Sequence[MultiAddr] = []

        # log file
        self.log_file = log_file or LIBP2P_NODE_LOG_FILE
        if not Path(self.log_file).is_absolute():
            self.log_file = os.path.join(data_dir, self.log_file)  # pragma: nocover
        # env file
        self.env_file = env_file or LIBP2P_NODE_ENV_FILE
        if not Path(self.env_file).is_absolute():
            self.env_file = os.path.join(data_dir, self.env_file)

        # named pipes (fifos)
        self.pipe: Optional[IPCChannel] = None
        self._loop: Optional[AbstractEventLoop] = None
        self.proc: Optional[subprocess.Popen] = None
        self._log_file_desc: Optional[IO[str]] = None

        self.logger = logger
        self._connection_timeout = connection_timeout or PIPE_CONN_TIMEOUT
        self._max_restarts = max_restarts
        self._restart_counter: int = 0
        self._is_on_stop: bool = False

    def _make_env_file(self, pipe_in_path: str, pipe_out_path: str) -> str:
        # setup config
        if os.path.exists(self.env_file):
            os.remove(self.env_file)  # pragma: nocover

        config = ""
        config += "AEA_AGENT_ADDR={}\n".format(self.address)
        config += "AEA_P2P_ID={}\n".format(self.key)
        config += "AEA_P2P_URI={}\n".format(str(self.uri))
        config += "AEA_P2P_ENTRY_URIS={}\n".format(
            ",".join(
                [
                    str(maddr)
                    for maddr in self.entry_peers
                    if str(maddr) != str(self.uri)  # TOFIX(LR) won't exclude self
                ]
            )
        )
        config += "NODE_TO_AEA={}\n".format(pipe_in_path)
        config += "AEA_TO_NODE={}\n".format(pipe_out_path)
        config += "AEA_P2P_URI_PUBLIC={}\n".format(
            str(self.public_uri) if self.public_uri is not None else ""
        )
        config += "AEA_P2P_DELEGATE_URI={}\n".format(
            str(self.delegate_uri) if self.delegate_uri is not None else ""
        )
        config += "AEA_P2P_URI_MONITORING={}\n".format(
            str(self.monitoring_uri) if self.monitoring_uri is not None else ""
        )
        config += "AEA_P2P_POR_ADDRESS={}\n".format(self.record.address)
        config += "AEA_P2P_POR_PUBKEY={}\n".format(self.record.public_key)
        config += "AEA_P2P_POR_PEER_PUBKEY={}\n".format(
            self.record.representative_public_key
        )
        config += "AEA_P2P_POR_SIGNATURE={}\n".format(self.record.signature)
        config += "AEA_P2P_POR_SERVICE_ID={}\n".format(POR_DEFAULT_SERVICE_ID)
        config += "AEA_P2P_POR_LEDGER_ID={}\n".format(self.record.ledger_id)
        config += "AEA_P2P_CFG_REGISTRATION_DELAY={}\n".format(
            str(self.peer_registration_delay)
            if self.peer_registration_delay is not None
            else str(0.0)
        )
        config += "AEA_P2P_CFG_STORAGE_PATH={}\n".format(
            self.records_storage_path if self.records_storage_path is not None else ""
        )

        config += "AEA_P2P_MAILBOX_URI={}\n".format(self.mailbox_uri)

        with open(self.env_file, "w") as env_file:  # overwrite if exists
            env_file.write(config)

        return config

    async def _set_connection_to_node(self) -> bool:
        if self.pipe is None:
            raise Exception("pipe was not set")  # pragma: nocover

        return await self.pipe.connect(timeout=self._connection_timeout)

    def get_client(self) -> NodeClient:
        """Get client instance to communicate to node."""
        if self.pipe is None:
            raise Exception("pipe was not set")  # pragma: nocover

        return NodeClient(self.pipe, self.record)

    def _child_watcher_callback(self, *_) -> None:  # type: ignore # pragma: nocover
        """Log if process was terminated before stop was called."""
        if self._is_on_stop or self.proc is None:
            return
        self.proc.poll()
        returncode = self.proc.returncode
        self.logger.error(
            f"Node process with pid {self.proc.pid} was terminated with returncode {returncode}"
        )

    def is_proccess_running(self) -> bool:
        """Check process is running."""
        if not self.proc:
            return False

        self.proc.poll()
        return self.proc.returncode is None

    async def start(self) -> None:
        """Start the node."""
        self._is_on_stop = False
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._log_file_desc = open(self.log_file, "a", 1)

        # tcp socket on every platform
        self.pipe = TCPSocketChannel(logger=self.logger)

        env_file_data = self._make_env_file(
            pipe_in_path=self.pipe.in_path, pipe_out_path=self.pipe.out_path
        )
        # run node
        self.logger.info("Starting libp2p node...")
        self.proc = _golang_module_run(
            self.source, LIBP2P_NODE_MODULE_NAME, [self.env_file], self._log_file_desc
        )

        if (
            platform.system() != "Windows"
            and sys.version_info.major == 3
            and sys.version_info.minor >= 8
        ):  # pragma: nocover
            with events.get_child_watcher() as watcher:
                if watcher:
                    watcher.add_child_handler(
                        self.proc.pid, self._child_watcher_callback
                    )

        self.logger.info("Connecting to libp2p node...")

        try:
            connected = await self._set_connection_to_node()

            if not connected:
                raise Exception("Couldn't connect to libp2p process within timeout")
        except Exception as e:
            err_msg = self.get_libp2p_node_error()
            self.logger.error("Couldn't connect to libp2p process: {}".format(err_msg))
            self.logger.error(
                "Libp2p process configuration:\n{}".format(env_file_data.strip())
            )
            if err_msg == "":
                with open(self.log_file, "r") as f:
                    self.logger.error(
                        "Libp2p process log file {}:\n{}".format(
                            self.log_file, f.read()
                        )
                    )
            else:  # pragma: nocover
                log_data = Path(self.log_file).read_text()
                self.logger.error(f"Failure to connect to Libp2pNode:\n{log_data}")

            await self.stop()
            raise e

        self.logger.info("Successfully connected to libp2p node!")
        self.multiaddrs = self.get_libp2p_node_multiaddrs()
        self.describe_configuration()

    async def restart(self) -> None:
        """Perform node restart."""
        if self._restart_counter >= self._max_restarts:
            raise ValueError(f"Max restarts attempts reached: {self._max_restarts}")
        await self.stop()
        await self.start()
        self._restart_counter += 1

    def describe_configuration(self) -> None:
        """Print a message describing the libp2p node configuration"""
        msg = LIBP2P_SUCCESS_MESSAGE

        if self.public_uri is not None:
            msg += "full DHT mode with "
            if self.delegate_uri is not None:  # pragma: nocover
                msg += "delegate service reachable at '{}:{}' and relay service enabled. ".format(
                    self.public_uri.host, self.delegate_uri.port
                )
            else:
                msg += "relay service enabled. "

            msg += "To join its network use multiaddr '{}'.".format(self.multiaddrs[0])
        else:
            msg += "relayed mode and cannot be used as entry peer."

        self.logger.info(msg)

    def get_libp2p_node_multiaddrs(self) -> Sequence[MultiAddr]:
        """
        Get the node's multiaddresses.

        :return: a list of multiaddresses
        """
        LIST_START = "MULTIADDRS_LIST_START"
        LIST_END = "MULTIADDRS_LIST_END"

        multiaddrs: List[MultiAddr] = []

        with open(self.log_file, "r") as f:
            lines = f.readlines()

        found = False
        for line in lines:
            if LIST_START in line:
                found = True
                multiaddrs = []
                continue
            if found:
                elem = line.strip()
                if elem != LIST_END and len(elem) != 0:
                    multiaddrs.append(MultiAddr.from_string(elem))
                else:
                    found = False
        return multiaddrs

    def get_libp2p_node_error(self) -> str:
        """
        Parses libp2p node logs for critical errors

        :return: error message if any, empty string otherwise
        """

        CRITICAL_ERROR = "LIBP2P_NODE_PANIC_ERROR"
        PANIC_ERROR = "panic:"

        error_msg = ""
        panic_msg = ""

        with open(self.log_file, "r") as f:
            lines = f.readlines()

        for line in lines:  # pragma: nocover
            if CRITICAL_ERROR in line:
                parts = line.split(":", 1)
                error_msg = parts[1].strip()
            if PANIC_ERROR in line:
                parts = line.split(":", 1)
                panic_msg = parts[1].strip()

        return error_msg if error_msg != "" else panic_msg

    async def stop(self) -> None:
        """Stop the node."""
        if self.proc is not None:
            self.logger.debug("Terminating node process {}...".format(self.proc.pid))
            self._is_on_stop = True
            self.proc.poll()
            self.proc.terminate()
            self.logger.debug(
                "Waiting for node process {} to terminate...".format(self.proc.pid)
            )
            self.proc.wait()
            if self._log_file_desc is None:
                raise ValueError("log file descriptor is not set.")  # pragma: nocover
            self._log_file_desc.close()
        else:
            self.logger.debug("Called stop when process not set!")  # pragma: no cover

        if self.pipe is not None:
            try:
                await self.pipe.close()
            except Exception as e:  # pragma: nocover pylint: disable=broad-except
                self.logger.exception(f"Failure during pipe closing. Exception: {e}")
            self.pipe = None
        else:
            self.logger.debug("Called stop when pipe not set!")  # pragma: no cover

        if os.path.exists(self.env_file):
            os.remove(self.env_file)


class P2PLibp2pConnection(Connection):
    """A libp2p p2p node connection."""

    connection_id = PUBLIC_ID
    DEFAULT_MAX_RESTARTS = 5

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a p2p libp2p connection."""
        super().__init__(**kwargs)
        ledger_id = self.configuration.config.get("ledger_id", DEFAULT_LEDGER)
        if ledger_id not in SUPPORTED_LEDGER_IDS:
            raise ValueError(  # pragma: nocover
                "Ledger id '{}' is not supported. Supported ids: '{}'".format(
                    ledger_id, SUPPORTED_LEDGER_IDS
                )
            )
        libp2p_local_uri: Optional[str] = self.configuration.config.get("local_uri")
        libp2p_public_uri: Optional[str] = self.configuration.config.get("public_uri")
        libp2p_delegate_uri: Optional[str] = self.configuration.config.get(
            "delegate_uri"
        )
        libp2p_monitoring_uri: Optional[str] = self.configuration.config.get(
            "monitoring_uri"
        )
        libp2p_entry_peers = self.configuration.config.get("entry_peers")
        if libp2p_entry_peers is None:
            libp2p_entry_peers = []
        libp2p_entry_peers = list(cast(List, libp2p_entry_peers))
        log_file: Optional[str] = self.configuration.config.get("log_file")
        env_file: Optional[str] = self.configuration.config.get("env_file")
        peer_registration_delay: Optional[str] = self.configuration.config.get(
            "peer_registration_delay"
        )
        records_storage_path: Optional[str] = self.configuration.config.get(
            "storage_path"
        )
        node_connection_timeout: Optional[float] = self.configuration.config.get(
            "node_connection_timeout", PIPE_CONN_TIMEOUT
        )
        if (
            self.has_crypto_store
            and self.crypto_store.crypto_objects.get(ledger_id, None) is not None
        ):  # pragma: no cover
            key = self.crypto_store.crypto_objects[ledger_id]
        else:
            raise ValueError(
                f"Couldn't find connection key for {str(ledger_id)} in connections keys. "
                "Please ensure agent private key is added with `aea add-key`."
            )

        uri = None
        if libp2p_local_uri is not None:
            uri = Uri(libp2p_local_uri)

        public_uri = None
        if libp2p_public_uri is not None:
            public_uri = Uri(libp2p_public_uri)

        delegate_uri = None
        if libp2p_delegate_uri is not None:  # pragma: nocover
            delegate_uri = Uri(libp2p_delegate_uri)

        monitoring_uri = None
        if libp2p_monitoring_uri is not None:
            monitoring_uri = Uri(libp2p_monitoring_uri)  # pragma: nocover

        entry_peers = [
            MultiAddr.from_string(str(maddr)) for maddr in libp2p_entry_peers
        ]

        delay = None
        if peer_registration_delay is not None:
            try:
                delay = float(peer_registration_delay)
            except ValueError:
                raise ValueError(
                    f"peer_registration_delay {peer_registration_delay} must be a float number in seconds"
                )

        if public_uri is None:
            # node will be run as a ClientDHT
            # requires entry peers to use as relay
            if entry_peers is None or len(entry_peers) == 0:
                raise ValueError(  # pragma: no cover
                    "At least one Entry Peer should be provided when node is run in relayed mode"
                )
            if delegate_uri is not None:  # pragma: no cover
                self.logger.warning(
                    "Ignoring Delegate Uri configuration as node is run in relayed mode"
                )
        else:
            # node will be run as a full NodeDHT
            if uri is None:
                raise ValueError(  # pragma: no cover
                    "Local Uri must be set when Public Uri is provided. "
                    "Hint: they are the same for local host/network deployment"
                )
            # check if node's public host and entry peers hosts are either
            #  both private or both public
            if not _ip_all_private_or_all_public(
                [public_uri.host] + [maddr.host for maddr in entry_peers]
            ):
                raise ValueError(  # pragma: nocover
                    "Node's public ip and entry peers ip addresses are not in the same ip address space (private/public)"
                )

        cert_requests = self.configuration.cert_requests
        if cert_requests is None or len(cert_requests) != 1:
            raise ValueError(  # pragma: no cover
                "cert_requests field must be set and contain exactly one entry!"
            )
        cert_request = cert_requests[0]

        agent_record = AgentRecord.from_cert_request(
            cert_request, self.address, key.public_key, Path(self.data_dir)
        )

        # libp2p local node
        self.logger.debug("Public key used by libp2p node: {}".format(key.public_key))

        if self.configuration.config.get("mailbox_uri"):
            mailbox_uri = str(self.configuration.config.get("mailbox_uri"))
        else:
            mailbox_uri = ""

        module_dir = self._check_node_built()
        self.node = Libp2pNode(
            agent_record,
            key,
            module_dir,
            self.data_dir,
            LIBP2P_NODE_CLARGS,
            uri,
            public_uri,
            delegate_uri,
            monitoring_uri,
            entry_peers,
            log_file,
            env_file,
            self.logger,
            delay,
            records_storage_path,
            node_connection_timeout,
            max_restarts=self.configuration.config.get(
                "max_node_restarts", self.DEFAULT_MAX_RESTARTS
            ),
            mailbox_uri=mailbox_uri,
        )

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._receive_from_node_task = None  # type: Optional[asyncio.Future]
        self._node_client: Optional[NodeClient] = None

        self._send_queue: Optional[asyncio.Queue] = None
        self._send_task: Optional[asyncio.Task] = None

    def _check_node_built(self) -> str:
        """Check node built."""
        if self.configuration.build_directory is None:
            raise ValueError("Connection Configuration build directory is not set!")

        libp2p_node_module_path = os.path.join(
            self.configuration.build_directory, LIBP2P_NODE_MODULE_NAME
        )
        enforce(
            os.path.exists(libp2p_node_module_path),
            f"Module {LIBP2P_NODE_MODULE_NAME} is not present in {self.configuration.build_directory}, please call the `aea build` command first!",
        )
        return self.configuration.build_directory

    async def connect(self) -> None:
        """Set up the connection."""
        if self.is_connected:
            return  # pragma: nocover
            # start libp2p node
        with self._connect_context():
            self.node.logger = self.logger
            await self._start_node()
            # starting receiving msgs
            self._in_queue = asyncio.Queue()
            self._send_queue = asyncio.Queue()
            self._receive_from_node_task = asyncio.ensure_future(
                self._receive_from_node(), loop=self.loop
            )
            self._send_task = self.loop.create_task(self._send_loop())

    async def _start_node(self) -> None:
        """Start node and set node client instance."""
        await self.node.start()
        self._node_client = self.node.get_client()

    async def _restart_node(self) -> None:
        """Stop and start node again."""
        await self.node.stop()
        await self._start_node()

    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        if self.is_disconnected:
            return  # pragma: nocover

        self.state = ConnectionStates.disconnecting
        try:

            if self._receive_from_node_task is not None:
                self._receive_from_node_task.cancel()
                self._receive_from_node_task = None

            if self._send_task is not None:
                self._send_task.cancel()
                self._send_task = None

            await self.node.stop()
            if self._in_queue is not None:
                self._in_queue.put_nowait(None)
            else:
                self.logger.debug(  # pragma: nocover
                    "Called disconnect when input queue not initialized."
                )
        finally:
            self.state = ConnectionStates.disconnected

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
            if envelope is None:  # pragma: nocover
                self.logger.debug("Received None.")
                return None
            return envelope
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def _send_envelope_with_node_client(self, envelope: Envelope) -> None:
        if not self._node_client:  # pragma: nocover
            raise ValueError(f"Node client not set! Can not send envelope: {envelope}")

        if not self.node.pipe:  # pragma: nocover
            raise ValueError("Node is not connected")

        try:
            await self._node_client.send_envelope(envelope)
            return
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise  # pragma: nocover
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception(
                f"Failed to send. Exception: {e}. Try recover connection to node and send again."
            )

        try:
            if self.node.is_proccess_running():
                await self.node.pipe.connect()
                await self._node_client.send_envelope(envelope)
                self.logger.debug("Envelope sent after reconnect to node")
                return
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise  # pragma: nocover
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception(
                f"Failed to send after pipe reconnect. Exception: {e}. Try recover connection to node and send again."
            )

        try:
            await self._restart_node()
            await self._node_client.send_envelope(envelope)
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise  # pragma: nocover
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception(
                f"Failed to send after node restart. Exception: {e}. Try recover connection to node and send again."
            )
            raise

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
        if not self._node_client:
            raise ValueError("Node is not connected!")  # pragma: nocover
        try:
            return await self._node_client.read_envelope()
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            raise  # pragma: nocover
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception(
                f"Failed to read. Exception: {e}. Try reconnect to node and read again."
            )

            await self._restart_node()
            return await self._node_client.read_envelope()

    async def _receive_from_node(self) -> None:
        """Receive data from node."""
        while True:
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover

            if not self._node_client:
                raise ValueError("Node is not connected!")  # pragma: nocover

            envelope = await self._read_envelope_from_node()
            if envelope is None:
                break
            self._in_queue.put_nowait(envelope)

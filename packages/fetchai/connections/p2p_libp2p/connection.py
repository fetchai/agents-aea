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
"""This module contains the p2p libp2p connection."""
import asyncio
import logging
import os
import platform
import subprocess  # nosec
from asyncio import AbstractEventLoop, CancelledError
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
from aea.helpers.pipe import IPCChannel, make_ipc_channel
from aea.mail.base import Envelope


_default_logger = logging.getLogger("aea.packages.fetchai.connections.p2p_libp2p")

LIBP2P_NODE_MODULE_NAME = "libp2p_node"

LIBP2P_NODE_MODULE = str(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), LIBP2P_NODE_MODULE_NAME)
)

if platform.system() == "Windows":  # pragma: nocover
    LIBP2P_NODE_MODULE_NAME += ".exe"

LIBP2P_NODE_LOG_FILE = "libp2p_node.log"

LIBP2P_NODE_ENV_FILE = ".env.libp2p"

LIBP2P_NODE_CLARGS = list()  # type: List[str]

LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT = 660  # time to download ~66Mb

PIPE_CONN_TIMEOUT = 10.0

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p:0.17.0")

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
    ):
        """
        Initialize a p2p libp2p node.

        :param agent_record: the agent proof-of-representation for peer.
        :param key: secp256k1 curve private key.
        :param module_path: the module path.
        :param clargs: the command line arguments for the libp2p node
        :param uri: libp2p node ip address and port number in format ipaddress:port.
        :param public_uri: libp2p node public ip address and port number in format ipaddress:port.
        :param delegate_uri: libp2p node delegate service ip address and port number in format ipaddress:port.
        :param monitoring_uri: libp2 node monitoring ip address and port in fromat ipaddress:port
        :param entry_peers: libp2p entry peers multiaddresses.
        :param log_file: the logfile path for the libp2p node
        :param env_file: the env file path for the exchange of environment variables
        :param logger: the logger.
        :param peer_registration_delay: add artificial delay to agent registration in seconds
        :param connection_timeout: the connection timeout of the node
        :param max_restarts: amount of node restarts during operation
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
        self.entry_peers = entry_peers if entry_peers is not None else []

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
        self.clargs = clargs if clargs is not None else []

        # node libp2p multiaddrs
        self.multiaddrs = []  # type: Sequence[MultiAddr]

        # log file
        self.log_file = log_file if log_file is not None else LIBP2P_NODE_LOG_FILE
        if not Path(self.log_file).is_absolute():
            self.log_file = os.path.join(data_dir, self.log_file)  # pragma: nocover
        # env file
        self.env_file = env_file if env_file is not None else LIBP2P_NODE_ENV_FILE
        if not Path(self.env_file).is_absolute():
            self.env_file = os.path.join(data_dir, self.env_file)

        # named pipes (fifos)
        self.pipe = None  # type: Optional[IPCChannel]

        self._loop = None  # type: Optional[AbstractEventLoop]
        self.proc = None  # type: Optional[subprocess.Popen]
        self._log_file_desc = None  # type: Optional[IO[str]]

        self._config = ""
        self.logger = logger
        self._connection_timeout = (
            connection_timeout if connection_timeout is not None else PIPE_CONN_TIMEOUT
        )
        self._max_restarts = max_restarts
        self._restart_counter: int = 0

    async def start(self) -> None:
        """
        Start the node.

        :return: None
        """
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        self._log_file_desc = open(self.log_file, "a", 1)
        self._log_file_desc.write("test")
        self._log_file_desc.flush()

        # setup fifos
        self.pipe = make_ipc_channel(logger=self.logger)

        # setup config
        if os.path.exists(self.env_file):
            os.remove(self.env_file)  # pragma: nocover
        self._config = ""
        with open(self.env_file, "a") as env_file:
            self._config += "AEA_AGENT_ADDR={}\n".format(self.address)
            self._config += "AEA_P2P_ID={}\n".format(self.key)
            self._config += "AEA_P2P_URI={}\n".format(str(self.uri))
            self._config += "AEA_P2P_ENTRY_URIS={}\n".format(
                ",".join(
                    [
                        str(maddr)
                        for maddr in self.entry_peers
                        if str(maddr) != str(self.uri)  # TOFIX(LR) won't exclude self
                    ]
                )
            )
            self._config += "NODE_TO_AEA={}\n".format(self.pipe.in_path)
            self._config += "AEA_TO_NODE={}\n".format(self.pipe.out_path)
            self._config += "AEA_P2P_URI_PUBLIC={}\n".format(
                str(self.public_uri) if self.public_uri is not None else ""
            )
            self._config += "AEA_P2P_DELEGATE_URI={}\n".format(
                str(self.delegate_uri) if self.delegate_uri is not None else ""
            )
            self._config += "AEA_P2P_URI_MONITORING={}\n".format(
                str(self.monitoring_uri) if self.monitoring_uri is not None else ""
            )
            self._config += "AEA_P2P_POR_ADDRESS={}\n".format(self.record.address)
            self._config += "AEA_P2P_POR_PUBKEY={}\n".format(self.record.public_key)
            self._config += "AEA_P2P_POR_PEER_PUBKEY={}\n".format(
                self.record.representative_public_key
            )
            self._config += "AEA_P2P_POR_SIGNATURE={}\n".format(self.record.signature)
            self._config += "AEA_P2P_POR_SERVICE_ID={}\n".format(POR_DEFAULT_SERVICE_ID)
            self._config += "AEA_P2P_POR_LEDGER_ID={}\n".format(self.record.ledger_id)
            self._config += "AEA_P2P_CFG_REGISTRATION_DELAY={}\n".format(
                str(self.peer_registration_delay)
                if self.peer_registration_delay is not None
                else str(0.0)
            )
            self._config += "AEA_P2P_CFG_STORAGE_PATH={}\n".format(
                self.records_storage_path
                if self.records_storage_path is not None
                else ""
            )
            env_file.write(self._config)

        # run node
        self.logger.info("Starting libp2p node...")
        self.proc = _golang_module_run(
            self.source, LIBP2P_NODE_MODULE_NAME, [self.env_file], self._log_file_desc
        )

        self.logger.info("Connecting to libp2p node...")

        try:
            connected = await self.pipe.connect(timeout=self._connection_timeout)
            if not connected:
                raise Exception("Couldn't connect to libp2p process within timeout")
        except Exception as e:
            err_msg = self.get_libp2p_node_error()
            self.logger.error("Couldn't connect to libp2p process: {}".format(err_msg))
            self.logger.error(
                "Libp2p process configuration:\n{}".format(self._config.strip())
            )
            if err_msg == "":
                with open(self.log_file, "r") as f:
                    self.logger.error(
                        "Libp2p process log file {}:\n{}".format(
                            self.log_file, f.read()
                        )
                    )
            else:  # pragma: nocover
                self.logger.error(
                    "Please check log file {} for more details.".format(self.log_file)
                )

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

    async def write(self, data: bytes) -> None:
        """
        Write to the writer stream.

        :param data: data to write to stream
        """
        if self.pipe is None:
            raise ValueError("pipe is not set.")  # pragma: nocover

        try:
            await self.pipe.write(data)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception(
                "Exception raised on message write. Try reconnect to node and write again."
            )
            await self.restart()
            await self.pipe.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read from the reader stream.

        :return: bytes
        """
        if self.pipe is None:
            raise ValueError("pipe is not set.")  # pragma: nocover
        try:
            return await self.pipe.read()
        except Exception as e:  # pragma: nocover pylint: disable=broad-except
            self.logger.exception(
                f"Failed to read. Exception: {e}. Try reconnect to node and read again."
            )
            await self.restart()
            try:
                return await self.pipe.read()
            except Exception:  # pragma: nocover pylint: disable=broad-except
                self.logger.exception(
                    f"Failed to read after node restart. Exception: {e}."
                )
                return None

    def describe_configuration(self) -> None:
        """Print a message discribing the libp2p node configuration"""
        msg = LIBP2P_SUCCESS_MESSAGE

        if self.public_uri is not None:
            msg += "full DHT mode with "
            if self.delegate_uri is not None:
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

        multiaddrs = []  # type: List[MultiAddr]

        lines = []
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

        lines = []
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
        """
        Stop the node.

        :return: None
        """
        if self.proc is not None:
            self.logger.debug("Terminating node process {}...".format(self.proc.pid))
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
                self.logger.exception((f"Failure during pipe closing. Exception: {e}"))
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
            "node_connection_timeout"
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
        if libp2p_delegate_uri is not None:
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
        )

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._receive_from_node_task = None  # type: Optional[asyncio.Future]

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
        """
        Set up the connection.

        :return: None
        """
        if self.is_connected:
            return  # pragma: nocover
        try:
            # start libp2p node
            self.state = ConnectionStates.connecting
            self.node.logger = self.logger
            await self.node.start()
            # starting receiving msgs
            self._in_queue = asyncio.Queue()
            self._receive_from_node_task = asyncio.ensure_future(
                self._receive_from_node(), loop=self.loop
            )
            self.state = ConnectionStates.connected
        except (CancelledError, Exception) as e:
            self.state = ConnectionStates.disconnected
            raise e

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        if self.is_disconnected:
            return  # pragma: nocover
        self.state = ConnectionStates.disconnecting
        if self._receive_from_node_task is not None:
            self._receive_from_node_task.cancel()
            self._receive_from_node_task = None
        await self.node.stop()
        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:
            self.logger.debug(  # pragma: nocover
                "Called disconnect when input queue not initialized."
            )
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
            if data is None:
                self.logger.debug("Received None.")
                return None
            self.logger.debug("Received data: {}".format(data))
            return Envelope.decode(data)
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: Envelope) -> None:
        """
        Send messages.

        :return: None
        """
        self._ensure_valid_envelope_for_external_comms(envelope)
        await self.node.write(envelope.encode())

    async def _receive_from_node(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        while True:
            data = await self.node.read()
            if self._in_queue is None:
                raise ValueError("Input queue not initialized.")  # pragma: nocover
            self._in_queue.put_nowait(data)
            if data is None:
                break

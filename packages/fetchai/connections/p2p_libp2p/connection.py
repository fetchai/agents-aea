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
import shutil
import subprocess  # nosec
import tempfile
from asyncio import AbstractEventLoop, CancelledError
from ipaddress import ip_address
from pathlib import Path
from random import randint
from socket import gethostbyname
from typing import IO, List, Optional, Sequence, cast

from aea.common import Address
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea.exceptions import enforce
from aea.helpers.multiaddr.base import MultiAddr
from aea.helpers.pipe import IPCChannel, make_ipc_channel
from aea.mail.base import Envelope


_default_logger = logging.getLogger("aea.packages.fetchai.connections.p2p_libp2p")

LIBP2P_NODE_MODULE = str(os.path.abspath(os.path.dirname(__file__)))

LIBP2P_NODE_MODULE_NAME = "libp2p_node"

if platform.system() == "Windows":  # pragma: nocover
    LIBP2P_NODE_MODULE_NAME += ".exe"

LIBP2P_NODE_LOG_FILE = "libp2p_node.log"

LIBP2P_NODE_ENV_FILE = ".env.libp2p"

LIBP2P_NODE_CLARGS = list()  # type: List[str]

LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT = 660  # time to download ~66Mb

PIPE_CONN_TIMEOUT = 10.0

# TOFIX(LR) not sure is needed
LIBP2P = "libp2p"

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p:0.13.0")

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]

LIBP2P_SUCCESS_MESSAGE = "Peer running in "


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


class Uri:
    """Holds a node address in format "host:port"."""

    def __init__(
        self,
        uri: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """Initialise Uri."""
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

    def __str__(self):
        """Get string representation."""
        return "{}:{}".format(self._host, self._port)

    def __repr__(self):  # pragma: no cover
        """Get object representation."""
        return self.__str__()

    @property
    def host(self) -> str:
        """Get host."""
        return self._host

    @property
    def port(self) -> int:
        """Get port."""
        return self._port


class Libp2pNode:
    """Libp2p p2p node as a subprocess with named pipes interface."""

    def __init__(
        self,
        agent_addr: Address,
        key: Crypto,
        module_path: str,
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
    ):
        """
        Initialize a p2p libp2p node.

        :param agent_addr: the agent address.
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
        """

        self.address = agent_addr

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

        # node startup
        self.source = os.path.abspath(module_path)
        self.clargs = clargs if clargs is not None else []

        # node libp2p multiaddrs
        self.multiaddrs = []  # type: Sequence[MultiAddr]

        # log file
        self.log_file = log_file if log_file is not None else LIBP2P_NODE_LOG_FILE
        self.log_file = os.path.join(os.path.abspath(os.getcwd()), self.log_file)

        # env file
        self.env_file = env_file if env_file is not None else LIBP2P_NODE_ENV_FILE
        self.env_file = os.path.join(os.path.abspath(os.getcwd()), self.env_file)

        # named pipes (fifos)
        self.pipe = None  # type: Optional[IPCChannel]

        self._loop = None  # type: Optional[AbstractEventLoop]
        self.proc = None  # type: Optional[subprocess.Popen]
        self._log_file_desc = None  # type: Optional[IO[str]]

        self._config = ""
        self.logger = logger
        self._connection_timeout = PIPE_CONN_TIMEOUT

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
            os.remove(self.env_file)
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
            self._config += "AEA_P2P_CFG_REGISTRATION_DELAY={}\n".format(
                str(self.peer_registration_delay)
                if self.peer_registration_delay is not None
                else str(0.0)
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

            self.stop()
            raise e

        self.logger.info("Successfully connected to libp2p node!")
        self.multiaddrs = self.get_libp2p_node_multiaddrs()
        self.describe_configuration()

    async def write(self, data: bytes) -> None:
        """
        Write to the writer stream.

        :param data: data to write to stream
        """
        if self.pipe is None:
            raise ValueError("pipe is not set.")  # pragma: nocover
        await self.pipe.write(data)

    async def read(self) -> Optional[bytes]:
        """
        Read from the reader stream.

        :return: bytes
        """
        if self.pipe is None:
            raise ValueError("pipe is not set.")  # pragma: nocover
        return await self.pipe.read()

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

    def stop(self) -> None:
        """
        Stop the node.

        :return: None
        """
        # TOFIX(LR) wait is blocking and proc can ignore terminate
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
        if os.path.exists(LIBP2P_NODE_ENV_FILE):
            os.remove(LIBP2P_NODE_ENV_FILE)


class P2PLibp2pConnection(Connection):
    """A libp2p p2p node connection."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize a p2p libp2p connection."""

        # we put it here so below we can access the address
        super().__init__(**kwargs)
        ledger_id = self.configuration.config.get("ledger_id", DEFAULT_LEDGER)
        if ledger_id not in SUPPORTED_LEDGER_IDS:
            raise ValueError(  # pragma: nocover
                "Ledger id '{}' is not supported. Supported ids: '{}'".format(
                    ledger_id, SUPPORTED_LEDGER_IDS
                )
            )
        libp2p_key_file = self.configuration.config.get(
            "node_key_file"
        )  # Optional[str]
        libp2p_local_uri = self.configuration.config.get("local_uri")  # Optional[str]
        libp2p_public_uri = self.configuration.config.get("public_uri")  # Optional[str]
        libp2p_delegate_uri = self.configuration.config.get(
            "delegate_uri"
        )  # Optional[str]
        libp2p_monitoring_uri = self.configuration.config.get(
            "monitoring_uri"
        )  # Optional[str]
        libp2p_entry_peers = self.configuration.config.get("entry_peers")
        if libp2p_entry_peers is None:
            libp2p_entry_peers = []
        libp2p_entry_peers = list(cast(List, libp2p_entry_peers))
        log_file = self.configuration.config.get("log_file")  # Optional[str]
        env_file = self.configuration.config.get("env_file")  # Optional[str]
        peer_registration_delay = self.configuration.config.get(
            "peer_registration_delay"
        )  # Optional[str]

        if (
            self.has_crypto_store
            and self.crypto_store.crypto_objects.get(ledger_id, None) is not None
        ):  # pragma: no cover
            key = self.crypto_store.crypto_objects[ledger_id]
        elif libp2p_key_file is not None:
            key = make_crypto(ledger_id, private_key_path=libp2p_key_file)
        else:
            key = make_crypto(ledger_id)

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
                raise ValueError(
                    "At least one Entry Peer should be provided when node is run in relayed mode"
                )
            if delegate_uri is not None:  # pragma: no cover
                self.logger.warning(
                    "Ignoring Delegate Uri configuration as node is run in relayed mode"
                )
        else:
            # node will be run as a full NodeDHT
            if uri is None:
                raise ValueError(
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

        # libp2p local node
        self.logger.debug("Public key used by libp2p node: {}".format(key.public_key))
        temp_dir = tempfile.mkdtemp()
        self.libp2p_workdir = os.path.join(temp_dir, "libp2p_workdir")

        self._check_node_built()
        self.node = Libp2pNode(
            self.address,
            key,
            self.configuration.build_directory,
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
        )

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._receive_from_node_task = None  # type: Optional[asyncio.Future]

    def _check_node_built(self) -> None:
        """Check node built and move it to workdir."""
        enforce(
            bool(self.configuration.build_directory),
            "Connection Configuration build directory is not set!",
        )

        libp2p_node_module_path = os.path.join(
            cast(str, self.configuration.build_directory), LIBP2P_NODE_MODULE_NAME
        )
        enforce(
            os.path.exists(libp2p_node_module_path),
            f"Module {LIBP2P_NODE_MODULE_NAME} does not present in {self.configuration.build_directory}, please call `aea build` command",
        )
        shutil.copy(libp2p_node_module_path, self.libp2p_workdir)

    @property
    def libp2p_address(self) -> str:  # pragma: no cover
        """The address used by the node."""
        return self.node.pub

    @property
    def libp2p_address_id(self) -> str:  # pragma: no cover
        """The identifier for the address."""
        return LIBP2P

    async def connect(self) -> None:
        """
        Set up the connection.

        :return: None
        """
        if self.is_connected:
            return  # pragma: nocover
        self._state.set(ConnectionStates.connecting)
        try:
            # start libp2p node
            self._state.set(ConnectionStates.connecting)
            self.node.logger = self.logger
            await self.node.start()
            # starting receiving msgs
            self._in_queue = asyncio.Queue()
            self._receive_from_node_task = asyncio.ensure_future(
                self._receive_from_node(), loop=self.loop
            )
            self._state.set(ConnectionStates.connected)
        except (CancelledError, Exception) as e:
            self._state.set(ConnectionStates.disconnected)
            raise e

    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        :return: None
        """
        if self.is_disconnected:
            return  # pragma: nocover
        self._state.set(ConnectionStates.disconnecting)
        if self._receive_from_node_task is not None:
            self._receive_from_node_task.cancel()
            self._receive_from_node_task = None
        self.node.stop()
        if self.libp2p_workdir is not None:
            shutil.rmtree(Path(self.libp2p_workdir).parent)
        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:
            self.logger.debug(  # pragma: nocover
                "Called disconnect when input queue not initialized."
            )
        self._state.set(ConnectionStates.disconnected)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
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
                self.node.stop()
                self._state.set(ConnectionStates.disconnected)
                return None
                # TOFIX(LR) attempt restarting the node?
            self.logger.debug("Received data: {}".format(data))
            return Envelope.decode(data)
        except CancelledError:  # pragma: no cover
            self.logger.debug("Receive cancelled.")
            return None
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            self.logger.exception(e)
            return None

    async def send(self, envelope: Envelope):
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

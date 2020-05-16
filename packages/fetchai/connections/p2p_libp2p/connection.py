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
import errno
import logging
import os
import shutil
import struct
import subprocess  # nosec
import sys
import tempfile
from asyncio import AbstractEventLoop, CancelledError
from random import randint
from typing import IO, List, Optional, Sequence, cast

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.crypto.fetchai import FetchAICrypto
from aea.mail.base import Address, Envelope

logger = logging.getLogger("aea.packages.fetchai.connections.p2p_libp2p")


WORK_DIR = os.getcwd()

LIBP2P_NODE_MODULE = str(os.path.abspath(os.path.dirname(__file__)))

LIBP2P_NODE_MODULE_NAME = "libp2p_node"

LIBP2P_NODE_LOG_FILE = "libp2p_node.log"

LIBP2P_NODE_ENV_FILE = ".env.libp2p"

LIBP2P_NODE_CLARGS = [
    str(os.path.join(WORK_DIR, LIBP2P_NODE_ENV_FILE))
]  # type: List[str]

LIBP2P = "libp2p"

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p:0.1.0")

MultiAddr = str

LIBP2P_IPFS_BOOTSTRAP_NODES = [
    MultiAddr(
        "/ip4/104.131.131.82/tcp/4001/ipfs/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ"
    )
]


# TOFIX(LR) error: Cannot add child handler, the child watcher does not have a loop attached
async def _async_golang_get_deps(
    src: str, loop: AbstractEventLoop
) -> asyncio.subprocess.Process:
    """
    Downloads dependencies of go 'src' file - asynchronous
    """
    cmd = ["go", "get", "-d", "-v", "./..."]

    try:
        logger.debug(cmd, loop)
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=os.path.dirname(src), loop=loop
        )  # nosec
    except Exception as e:
        logger.error("While executing go get : {}".format(str(e)))
        raise e

    return proc


def _golang_module_build(path: str, log_file_desc: IO[str]) -> subprocess.Popen:
    """
    Builds go module located at `path`, downloads necessary dependencies
    """
    cmd = ["go", "build"]

    env = os.environ

    try:
        logger.debug(cmd)
        proc = subprocess.Popen(  # nosec
            cmd,
            env=env,
            cwd=path,
            stdout=log_file_desc,
            stderr=log_file_desc,
            shell=False,
        )
    except Exception as e:
        logger.error("While executing go build {} : {}".format(path, str(e)))
        raise e

    return proc


def _golang_module_run(
    path: str, name: str, args: Sequence[str], log_file_desc: IO[str]
) -> subprocess.Popen:
    """
    Runs a built module located at `path`
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

    def __repr__(self):
        return self.__str__()

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port


class Libp2pNode:
    """
    Libp2p p2p node as a subprocess with named pipes interface
    """

    def __init__(
        self,
        key: FetchAICrypto,
        module_path: str,
        clargs: Optional[List[str]] = None,
        uri: Optional[Uri] = None,
        entry_peers: Optional[Sequence[MultiAddr]] = None,
        log_file: Optional[str] = None,
        env_file: Optional[str] = None,
    ):
        """
        Initialize a p2p libp2p node.

        :param key: FET secp256k1 curve private key.
        :param source: the source path
        :param clargs: the command line arguments for the libp2p node
        :param uri: libp2p node ip address and port number in format ipaddress:port.
        :param entry_peers: libp2p entry peers multiaddresses.
        :param log_file: the logfile path for the libp2p node
        :param env_file: the env file path for the exchange of environment variables
        """

        # node id in the p2p network
        self.key = key.entity.private_key_hex
        self.pub = key.public_key

        # node uri
        self.uri = uri if uri is not None else Uri()

        # entry p
        self.entry_peers = entry_peers if entry_peers is not None else []

        # node startup
        self.source = os.path.abspath(module_path)
        self.clargs = clargs if clargs is not None else []

        # log file
        self.log_file = log_file if log_file is not None else LIBP2P_NODE_LOG_FILE

        # env file
        self.env_file = env_file if env_file is not None else LIBP2P_NODE_ENV_FILE

        # named pipes (fifos)
        tmp_dir = tempfile.mkdtemp()
        self.libp2p_to_aea_path = "{}/{}-libp2p_to_aea".format(tmp_dir, self.pub[:5])
        self.aea_to_libp2p_path = "{}/{}-aea_to_libp2p".format(tmp_dir, self.pub[:5])
        self._libp2p_to_aea = -1
        self._aea_to_libp2p = -1
        self._connection_attempts = 30

        self._loop = None  # type: Optional[AbstractEventLoop]
        self.proc = None  # type: Optional[subprocess.Popen]
        self._stream_reader = None  # type: Optional[asyncio.StreamReader]

    async def start(self) -> None:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        # open log file
        self._log_file_desc = open(self.log_file, "a", 1)

        # build the node
        # TOFIX(LR) fix async version
        logger.info("Downloading golang dependencies. This may take a while...")
        proc = _golang_module_build(self.source, self._log_file_desc)
        proc.wait()
        logger.info("Finished downloading golang dependencies.")

        # setup fifos
        in_path = self.libp2p_to_aea_path
        out_path = self.aea_to_libp2p_path
        logger.debug("Creating pipes ({}, {})...".format(in_path, out_path))
        if os.path.exists(in_path):
            os.remove(in_path)
        if os.path.exists(out_path):
            os.remove(out_path)
        os.mkfifo(in_path)
        os.mkfifo(out_path)

        # setup config
        if os.path.exists(LIBP2P_NODE_ENV_FILE):
            os.remove(LIBP2P_NODE_ENV_FILE)
        with open(LIBP2P_NODE_ENV_FILE, "a") as env_file:
            env_file.write("AEA_P2P_ID={}\n".format(self.key))
            env_file.write("AEA_P2P_URI={}\n".format(str(self.uri)))
            env_file.write(
                "AEA_P2P_ENTRY_URIS={}\n".format(
                    ",".join(
                        [
                            str(maddr)
                            for maddr in self.entry_peers
                            if str(maddr)
                            != str(self.uri)  # TOFIX(LR) won't exclude self
                        ]
                    )
                )
            )
            env_file.write("NODE_TO_AEA={}\n".format(in_path))
            env_file.write("AEA_TO_NODE={}\n".format(out_path))

        # run node
        logger.info("Starting libp2p node...")
        self.proc = _golang_module_run(self.source, LIBP2P_NODE_MODULE_NAME, self.clargs, self._log_file_desc)

        logger.info("Connecting to libp2p node...")
        await self._connect()

    async def _connect(self) -> None:
        if self._connection_attempts == 1:
            raise Exception("Couldn't connect to libp2p p2p process")
            # TOFIX(LR) use proper exception
        self._connection_attempts -= 1

        logger.debug(
            "Attempt opening pipes {}, {}...".format(
                self.libp2p_to_aea_path, self.aea_to_libp2p_path
            )
        )

        self._libp2p_to_aea = os.open(
            self.libp2p_to_aea_path, os.O_RDONLY | os.O_NONBLOCK
        )

        try:
            self._aea_to_libp2p = os.open(
                self.aea_to_libp2p_path, os.O_WRONLY | os.O_NONBLOCK
            )
        except OSError as e:
            if e.errno == errno.ENXIO:
                logger.debug(e)
                await asyncio.sleep(2)
                await self._connect()
                return
            else:
                raise e

        # setup reader
        assert (
            self._libp2p_to_aea != -1
            and self._aea_to_libp2p != -1
            and self._loop is not None
        ), "Incomplete initialization."
        self._stream_reader = asyncio.StreamReader(loop=self._loop)
        self._reader_protocol = asyncio.StreamReaderProtocol(
            self._stream_reader, loop=self._loop
        )
        self._fileobj = os.fdopen(self._libp2p_to_aea, "r")
        await self._loop.connect_read_pipe(lambda: self._reader_protocol, self._fileobj)

        logger.info("Successfully connected to libp2p node!")

    @asyncio.coroutine
    def write(self, data: bytes) -> None:
        size = struct.pack("!I", len(data))
        os.write(self._aea_to_libp2p, size)
        os.write(self._aea_to_libp2p, data)
        # TOFIX(LR) can use asyncio.connect_write_pipe

    async def read(self) -> Optional[bytes]:
        assert (
            self._stream_reader is not None
        ), "StreamReader not set, call connect first!"
        try:
            logger.debug("Waiting for messages...")
            buf = await self._stream_reader.readexactly(4)
            if not buf:
                return None
            size = struct.unpack("!I", buf)[0]
            data = await self._stream_reader.readexactly(size)
            if not data:
                return None
            return data
        except asyncio.streams.IncompleteReadError as e:
            logger.info(
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None

    def stop(self) -> None:
        # TOFIX(LR) wait is blocking and proc can ignore terminate
        if self.proc is not None:
            logger.debug("Terminating node process {}...".format(self.proc.pid))
            self.proc.terminate()
            logger.debug("Waiting for node process {} to terminate...".format(self.proc.pid))
            self.proc.wait()
        else:
            logger.debug("Called stop when process not set!")
        if os.path.exists(LIBP2P_NODE_ENV_FILE):
            os.remove(LIBP2P_NODE_ENV_FILE)


class P2PLibp2pConnection(Connection):
    """A libp2p p2p node connection.
    """

    def __init__(
        self,
        key: FetchAICrypto,
        uri: Optional[Uri] = None,
        entry_peers: Optional[Sequence[MultiAddr]] = None,
        log_file: Optional[str] = None,
        env_file: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a p2p libp2p connection.

        :param key: FET sepc256k1 curve private key.
        :param uri: libp2p node ip address and port number in format ipaddress:port.
        :param entry_peers: libp2p entry peers multiaddresses.
        :param log_file: libp2p node log file
        """
        self._check_go_installed()
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PUBLIC_ID
        # libp2p local node
        logger.debug("Public key used by libp2p node: {}".format(key.public_key))
        # use ipfs public dht to bootstrap
        bootstrap_peers = LIBP2P_IPFS_BOOTSTRAP_NODES
        if entry_peers is not None:
            bootstrap_peers.extend(entry_peers)
        self.node = Libp2pNode(
            key,
            LIBP2P_NODE_MODULE,
            LIBP2P_NODE_CLARGS,
            uri,
            bootstrap_peers,
            log_file,
            env_file,
        )
        # replace address in kwargs
        kwargs["address"] = self.node.pub
        super().__init__(**kwargs)

        if uri is None and (entry_peers is None or len(entry_peers) == 0):
            raise ValueError("Uri parameter must be set for genesis connection")

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._receive_from_node_task = None  # type: Optional[asyncio.Future]

    @property
    def libp2p_address(self) -> str:
        """The address used by the node."""
        return self.node.pub

    @property
    def libp2p_address_id(self) -> str:
        """The identifier for the address."""
        return LIBP2P

    async def connect(self) -> None:
        """
        Set up the connection.

        :return: None
        """
        if self.connection_status.is_connected:
            return
        try:
            # start libp2p node
            self.connection_status.is_connecting = True
            await self.node.start()
            self.connection_status.is_connecting = False
            self.connection_status.is_connected = True

            # starting receiving msgs
            self._in_queue = asyncio.Queue()
            self._receive_from_node_task = asyncio.ensure_future(
                self._receive_from_node(), loop=self._loop
            )
        except (CancelledError, Exception) as e:
            self.connection_status.is_connected = False
            raise e

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
        if self._receive_from_node_task is not None:
            self._receive_from_node_task.cancel()
            self._receive_from_node_task = None
        self.node.stop()
        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:
            logger.debug("Called disconnect when input queue not initialized.")

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        try:
            assert self._in_queue is not None, "Input queue not initialized."
            data = await self._in_queue.get()
            if data is None:
                logger.debug("Received None.")
                self.node.stop()
                self.connection_status.is_connected = False
                return None
                # TOFIX(LR) attempt restarting the node?
            logger.debug("Received data: {}".format(data))
            return Envelope.decode(data)
        except CancelledError:
            logger.debug("Receive cancelled.")
            return None
        except Exception as e:
            logger.exception(e)
            return None

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        await self.node.write(envelope.encode())

    async def _receive_from_node(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        while True:
            data = await self.node.read()
            if data is None:
                break
            assert self._in_queue is not None, "Input queue not initialized."
            self._in_queue.put_nowait(data)

    def _check_go_installed(self) -> None:
        """Checks if go is installed. Sys.exits if not"""
        res = shutil.which("go")
        if res is None:
            logger.error(
                "Please install go before running the `fetchai/p2p_libp2p:0.1.0` connection. "
                "Go is available for download here: https://golang.org/doc/install"
            )
            sys.exit(1)

    @classmethod
    def from_config(
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the stub connection from the connection configuration.

        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        fet_key_file = configuration.config.get("fet_key_file")  # Optional[str]
        libp2p_host = configuration.config.get("libp2p_host")  # Optional[str]
        libp2p_port = configuration.config.get("libp2p_port")  # Optional[int]
        entry_peers = list(cast(List, configuration.config.get("libp2p_entry_peers")))
        log_file = configuration.config.get("libp2p_log_file")  # Optional[str]
        env_file = configuration.config.get("libp2p_env_file")  # Optional[str]

        if fet_key_file is None:
            key = FetchAICrypto()
        else:
            key = FetchAICrypto(fet_key_file)

        uri = None
        if libp2p_port is not None:
            if libp2p_host is not None:
                uri = Uri(host=libp2p_host, port=libp2p_port)
            else:
                uri = Uri(host="127.0.0.1", port=libp2p_port)

        entry_peers_maddrs = [MultiAddr(maddr) for maddr in entry_peers]

        return P2PLibp2pConnection(
            key,
            uri,
            entry_peers_maddrs,
            log_file,
            env_file,
            address=address,
            configuration=configuration,
        )

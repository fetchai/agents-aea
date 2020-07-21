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
import distutils
import errno
import logging
import os
import shutil
import struct
import subprocess  # nosec
import tempfile
from asyncio import AbstractEventLoop, CancelledError
from random import randint
from threading import Thread
from typing import IO, List, Optional, Sequence, cast

from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea.exceptions import AEAException
from aea.mail.base import Address, Envelope

logger = logging.getLogger("aea.packages.fetchai.connections.p2p_libp2p")

LIBP2P_NODE_MODULE = str(os.path.abspath(os.path.dirname(__file__)))

LIBP2P_NODE_MODULE_NAME = "libp2p_node"

LIBP2P_NODE_LOG_FILE = "libp2p_node.log"

LIBP2P_NODE_ENV_FILE = ".env.libp2p"

LIBP2P_NODE_CLARGS = list()  # type: List[str]

LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT = 660  # time to download ~66Mb

# TOFIX(LR) not sure is needed
LIBP2P = "libp2p"

PUBLIC_ID = PublicId.from_str("fetchai/p2p_libp2p:0.5.0")

MultiAddr = str

SUPPORTED_LEDGER_IDS = ["fetchai", "cosmos", "ethereum"]


async def _golang_module_build_async(
    path: str,
    log_file_desc: IO[str],
    loop: Optional[asyncio.AbstractEventLoop] = None,
    timeout: float = LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT,
) -> int:
    """
    Builds go module located at `path`, downloads necessary dependencies

    :return: build command returncode
    """
    cmd = ["go", "build"]

    env = os.environ

    proc = AwaitableProc(
        cmd, env=env, cwd=path, stdout=log_file_desc, stderr=log_file_desc, shell=False,
    )

    golang_build = asyncio.ensure_future(proc.start())

    try:
        returncode = await asyncio.wait_for(golang_build, timeout)
    except asyncio.TimeoutError:
        e = Exception(
            "Failed to download libp2p dependencies within timeout({})".format(
                LIBP2P_NODE_DEPS_DOWNLOAD_TIMEOUT
            )
        )
        logger.error(e)
        golang_build.cancel()
        raise e

    return returncode


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


class AwaitableProc:
    """
    Async-friendly subprocess.Popen
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.proc = None
        self._thread = None
        self.loop = None
        self.future = None

    async def start(self):
        """Start the subprocess"""
        self.proc = subprocess.Popen(*self.args, **self.kwargs)  # nosec
        self.loop = asyncio.get_event_loop()
        self.future = asyncio.futures.Future()
        self._thread = Thread(target=self._in_thread)
        self._thread.start()
        try:
            return await asyncio.shield(self.future)
        except asyncio.CancelledError:
            self.proc.terminate()
            return await self.future
        finally:
            self._thread.join()

    def _in_thread(self):
        self.proc.wait()
        self.loop.call_soon_threadsafe(self.future.set_result, self.proc.returncode)


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


class Libp2pNode:
    """
    Libp2p p2p node as a subprocess with named pipes interface
    """

    def __init__(
        self,
        agent_addr: Address,
        key: Crypto,
        module_path: str,
        clargs: Optional[List[str]] = None,
        uri: Optional[Uri] = None,
        public_uri: Optional[Uri] = None,
        delegate_uri: Optional[Uri] = None,
        entry_peers: Optional[Sequence[MultiAddr]] = None,
        log_file: Optional[str] = None,
        env_file: Optional[str] = None,
    ):
        """
        Initialize a p2p libp2p node.

        :param key: secp256k1 curve private key.
        :param source: the source path
        :param clargs: the command line arguments for the libp2p node
        :param uri: libp2p node ip address and port number in format ipaddress:port.
        :param public_uri: libp2p node public ip address and port number in format ipaddress:port.
        :param delegation_uri: libp2p node delegate service ip address and port number in format ipaddress:port.
        :param entry_peers: libp2p entry peers multiaddresses.
        :param log_file: the logfile path for the libp2p node
        :param env_file: the env file path for the exchange of environment variables
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

        # entry peer
        self.entry_peers = entry_peers if entry_peers is not None else []

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
        tmp_dir = tempfile.mkdtemp()
        self.libp2p_to_aea_path = "{}/{}-libp2p_to_aea".format(tmp_dir, self.pub[:5])
        self.aea_to_libp2p_path = "{}/{}-aea_to_libp2p".format(tmp_dir, self.pub[:5])
        self._libp2p_to_aea = -1
        self._aea_to_libp2p = -1
        self._connection_attempts = 10
        self._connection_timeout = 1.0

        self._loop = None  # type: Optional[AbstractEventLoop]
        self.proc = None  # type: Optional[subprocess.Popen]
        self._stream_reader = None  # type: Optional[asyncio.StreamReader]
        self._log_file_desc = None  # type: Optional[IO[str]]
        self._reader_protocol = None  # type: Optional[asyncio.StreamReaderProtocol]
        self._fileobj = None  # type: Optional[IO[str]]

        self.logger = logger

    @property
    def reader_protocol(self) -> asyncio.StreamReaderProtocol:
        """Get reader protocol."""
        assert self._reader_protocol is not None, "reader protocol not set!"
        return self._reader_protocol

    async def start(self) -> None:
        """
        Start the node.

        :return: None
        """
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        # open log file
        self._log_file_desc = open(self.log_file, "a", 1)

        # build the node
        # TOFIX(LR) fix async version
        logger.info("Downloading golang dependencies. This may take a while...")
        returncode = await _golang_module_build_async(self.source, self._log_file_desc)
        with open(self.log_file, "r") as f:
            self.logger.debug(f.read())
        node_log = ""
        with open(self.log_file, "r") as f:
            node_log = f.read()
        if returncode != 0:
            raise Exception(
                "Error while downloading golang dependencies and building it: {}, {}".format(
                    returncode, node_log
                )
            )
        self.logger.info("Finished downloading golang dependencies.")

        # setup fifos
        in_path = self.libp2p_to_aea_path
        out_path = self.aea_to_libp2p_path
        self.logger.debug("Creating pipes ({}, {})...".format(in_path, out_path))
        if os.path.exists(in_path):
            os.remove(in_path)  # pragma: no cover
        if os.path.exists(out_path):
            os.remove(out_path)  # pragma: no cover
        os.mkfifo(in_path)
        os.mkfifo(out_path)

        # setup config
        if os.path.exists(self.env_file):
            os.remove(self.env_file)
        with open(self.env_file, "a") as env_file:
            env_file.write("AEA_AGENT_ADDR={}\n".format(self.address))
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
            env_file.write(
                "AEA_P2P_URI_PUBLIC={}\n".format(
                    str(self.public_uri) if self.public_uri is not None else ""
                )
            )
            env_file.write(
                "AEA_P2P_DELEGATE_URI={}\n".format(
                    str(self.delegate_uri) if self.delegate_uri is not None else ""
                )
            )

        # run node
        self.logger.info("Starting libp2p node...")
        self.proc = _golang_module_run(
            self.source, LIBP2P_NODE_MODULE_NAME, [self.env_file], self._log_file_desc
        )

        self.logger.info("Connecting to libp2p node...")
        await self._connect()

    async def _connect(self) -> None:
        """
        Connnect to the peer node.

        :return: None
        """
        if self._connection_attempts == 1:
            with open(self.log_file, "r") as f:
                self.logger.debug("Couldn't connect to libp2p p2p process, logs:")
                self.logger.debug(f.read())
            raise Exception("Couldn't connect to libp2p p2p process")
            # TOFIX(LR) use proper exception
        self._connection_attempts -= 1

        self.logger.debug(
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
                logger.debug("Sleeping for {}...".format(self._connection_timeout))
                await asyncio.sleep(self._connection_timeout)
                await self._connect()
                return
            else:
                raise e  # pragma: no cover

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
        await self._loop.connect_read_pipe(lambda: self.reader_protocol, self._fileobj)

        self.logger.info("Successfully connected to libp2p node!")
        self.multiaddrs = self.get_libp2p_node_multiaddrs()
        self.logger.info("My libp2p addresses: {}".format(self.multiaddrs))

    @asyncio.coroutine
    def write(self, data: bytes) -> None:
        """
        Write to the writer stream.

        :param data: data to write to stream
        """
        size = struct.pack("!I", len(data))
        os.write(self._aea_to_libp2p, size)
        os.write(self._aea_to_libp2p, data)
        # TOFIX(LR) can use asyncio.connect_write_pipe

    async def read(self) -> Optional[bytes]:
        """
        Read from the reader stream.

        :return: bytes
        """
        assert (
            self._stream_reader is not None
        ), "StreamReader not set, call connect first!"
        try:
            self.logger.debug("Waiting for messages...")
            buf = await self._stream_reader.readexactly(4)
            if not buf:  # pragma: no cover
                return None
            size = struct.unpack("!I", buf)[0]
            data = await self._stream_reader.readexactly(size)
            if not data:  # pragma: no cover
                return None
            return data
        except asyncio.streams.IncompleteReadError as e:
            self.logger.info(  # pragma: nocover
                "Connection disconnected while reading from node ({}/{})".format(
                    len(e.partial), e.expected
                )
            )
            return None  # pragma: nocover

    # TOFIX(LR) hack, need to import multihash library and compute multiaddr from uri and public key
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
                if elem != LIST_END:
                    multiaddrs.append(MultiAddr(elem))
                else:
                    found = False
        return multiaddrs

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
        else:
            self.logger.debug("Called stop when process not set!")  # pragma: no cover
        if os.path.exists(LIBP2P_NODE_ENV_FILE):
            os.remove(LIBP2P_NODE_ENV_FILE)


class P2PLibp2pConnection(Connection):
    """A libp2p p2p node connection."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs):
        """Initialize a p2p libp2p connection."""

        self._check_go_installed()
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
        libp2p_entry_peers = self.configuration.config.get("entry_peers")
        if libp2p_entry_peers is None:
            libp2p_entry_peers = []
        libp2p_entry_peers = list(cast(List, libp2p_entry_peers))
        log_file = self.configuration.config.get("log_file")  # Optional[str]
        env_file = self.configuration.config.get("env_file")  # Optional[str]

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

        entry_peers = [MultiAddr(maddr) for maddr in libp2p_entry_peers]
        # TOFIX(LR) Make sure that this node is reachable in the case where
        #   fetchai's public dht nodes are used as entry peer and public
        #   uri is provided.
        #   Otherwise, it may impact the proper functioning of the dht

        if public_uri is None:
            # node will be run as a ClientDHT
            # requires entry peers to use as relay
            if entry_peers is None or len(entry_peers) == 0:
                raise ValueError(
                    "At least one Entry Peer should be provided when node can not be publically reachable"
                )
            if delegate_uri is not None:  # pragma: no cover
                logger.warning(
                    "Ignoring Delegate Uri configuration as node can not be publically reachable"
                )
        else:
            # node will be run as a full NodeDHT
            if uri is None:
                raise ValueError(
                    "Local Uri must be set when Public Uri is provided. "
                    "Hint: they are the same for local host/network deployment"
                )

        # libp2p local node
        logger.debug("Public key used by libp2p node: {}".format(key.public_key))
        self.libp2p_workdir = tempfile.mkdtemp()
        distutils.dir_util.copy_tree(LIBP2P_NODE_MODULE, self.libp2p_workdir)

        self.node = Libp2pNode(
            self.address,
            key,
            self.libp2p_workdir,
            LIBP2P_NODE_CLARGS,
            uri,
            public_uri,
            delegate_uri,
            entry_peers,
            log_file,
            env_file,
        )

        self._in_queue = None  # type: Optional[asyncio.Queue]
        self._receive_from_node_task = None  # type: Optional[asyncio.Future]

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
        if self.connection_status.is_connected:  # pragma: no cover
            return
        try:
            # start libp2p node
            self.connection_status.is_connecting = True
            self.node.logger = self.logger
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
        if self.libp2p_workdir is not None:
            distutils.dir_util.remove_tree(self.libp2p_workdir)
        if self._in_queue is not None:
            self._in_queue.put_nowait(None)
        else:
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
                self.node.stop()
                self.connection_status.is_connected = False
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
        await self.node.write(envelope.encode())

    async def _receive_from_node(self) -> None:
        """
        Receive data from node.

        :return: None
        """
        while True:
            data = await self.node.read()
            assert self._in_queue is not None, "Input queue not initialized."
            self._in_queue.put_nowait(data)
            if data is None:
                break

    @staticmethod
    def _check_go_installed() -> None:
        """Checks if go is installed. Sys.exits if not"""
        res = shutil.which("go")
        if res is None:
            raise AEAException(  # pragma: nocover
                "Please install go before running the `fetchai/p2p_libp2p:0.1.0` connection. "
                "Go is available for download here: https://golang.org/doc/install"
            )

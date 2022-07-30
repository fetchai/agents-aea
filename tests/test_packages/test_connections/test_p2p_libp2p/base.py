# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Constants, utility functions and base classes for ACN p2p_libp2p tests"""

import atexit
import functools
import inspect
import itertools
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
from unittest import mock

import yaml

from aea.configurations.base import ConnectionConfig
from aea.connections.base import Connection
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea.crypto.wallet import CryptoStore
from aea.helpers.base import CertRequest, SimpleId
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.valory.connections import p2p_libp2p_client
from packages.valory.connections.p2p_libp2p.check_dependencies import build_node
from packages.valory.connections.p2p_libp2p.connection import (
    LIBP2P_NODE_MODULE_NAME,
    MultiAddr,
    P2PLibp2pConnection,
    POR_DEFAULT_SERVICE_ID,
)
from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
)
from packages.valory.connections.p2p_libp2p_client.connection import (
    P2PLibp2pClientConnection,
)
from packages.valory.connections.p2p_libp2p_mailbox.connection import (
    P2PLibp2pMailboxConnection,
)

from tests.common.utils import wait_for_condition
from tests.conftest import (
    CosmosCrypto,
    DEFAULT_HOST,
    DEFAULT_LEDGER,
    EthereumCrypto,
    remove_test_directory,
)


TIMEOUT = 20
TEMP_LIBP2P_TEST_DIR = tempfile.mkdtemp()
ports = itertools.count(10234)

MockDefaultMessageProtocol = mock.Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@functools.lru_cache()
def load_client_connection_yaml_config() -> Dict[str, Any]:
    """Load libp2p client connection yaml configuration"""

    module_path = os.path.sep.join(p2p_libp2p_client.__package__.split("."))
    connection_yaml = Path(module_path).absolute() / "connection.yaml"
    config = yaml.safe_load(connection_yaml.read_text())["config"]
    dns_template = "/dns4/{domain}/tcp/{port}/p2p/{peer_id}"

    # add matching information needed in ACN libp2p tests
    port_mapping = {
        "9005": ("9003", "16Uiu2HAm9ftkcmsBwPf2KXjrUd9G6GPi2WN3opXvjrjukNpE9e5k"),
        "9006": ("9004", "16Uiu2HAmAzQL3YV2Yv37ffafuMaaPtLUSPBEoyjDyFyrcLQzgB6P"),
    }

    for node in config["nodes"]:
        domain, port = node["uri"].split(":")
        port, peer_id = port_mapping[port]
        node["maddr"] = dns_template.format(domain=domain, port=port, peer_id=peer_id)

    return config


LIBP2P_LEDGER = load_client_connection_yaml_config()["ledger_id"]


def create_data_dir() -> str:
    """Create data directory in temporary libp2p test directory"""
    subdir = Path(tempfile.mkdtemp()).parts[-1]
    data_dir = Path(TEMP_LIBP2P_TEST_DIR) / subdir
    Path(data_dir).mkdir(parents=True, exist_ok=False)
    return str(data_dir)


def create_identity(crypto) -> Identity:
    """Create identity for ACN libp2p tests"""

    identity = Identity(
        name="identity",
        address=crypto.address,
        public_key=crypto.public_key,
        default_address_key=crypto.identifier,
    )

    return identity


def make_cert_request(
    public_key: str, ledger_id: Union[SimpleId, str], path_prefix: str
) -> CertRequest:
    """Make cert request for ACN proof of representation (POR)"""

    cert_request = CertRequest(
        public_key=public_key,
        identifier=POR_DEFAULT_SERVICE_ID,
        ledger_id=ledger_id,
        not_before=LIBP2P_CERT_NOT_BEFORE,
        not_after=LIBP2P_CERT_NOT_AFTER,
        message_format="{public_key}",
        save_path=f"./{path_prefix}_cert.txt",
    )

    return cert_request


def _process_cert(key: Crypto, cert: CertRequest, path_prefix: str):
    # must match aea/cli/issue_certificates.py:_process_certificate
    assert cert.public_key is not None
    message = cert.get_message(cert.public_key)
    signature = key.sign_message(message).encode("ascii").hex()
    Path(cert.get_absolute_save_path(path_prefix)).write_bytes(
        signature.encode("ascii")
    )


def _make_libp2p_connection(
    data_dir: Optional[str] = None,
    port: Optional[int] = None,
    host: Optional[str] = DEFAULT_HOST,
    relay: bool = True,
    delegate: bool = False,
    mailbox: bool = False,
    entry_peers: Optional[Sequence[MultiAddr]] = None,
    delegate_port: Optional[int] = None,
    delegate_host: Optional[str] = DEFAULT_HOST,
    mailbox_port: Optional[int] = None,
    mailbox_host: Optional[str] = DEFAULT_HOST,
    agent_key: Optional[Crypto] = None,
    build_directory: Optional[str] = None,
    peer_registration_delay: str = "0.0",
) -> P2PLibp2pConnection:
    """Get a libp2p connection."""

    data_dir = data_dir or create_data_dir()
    log_file = os.path.join(data_dir, f"libp2p_node_{port}.log")
    if os.path.exists(log_file):
        os.remove(log_file)

    agent_key = agent_key or make_crypto(DEFAULT_LEDGER)
    identity = create_identity(agent_key)

    node_key = make_crypto(LIBP2P_LEDGER)
    node_key_path = os.path.join(data_dir, f"{node_key.public_key}.txt")
    node_key.dump(node_key_path)
    conn_crypto_store = CryptoStore({node_key.identifier: node_key_path})
    peer_public_key = conn_crypto_store.public_keys[LIBP2P_LEDGER]

    cert_request = make_cert_request(
        peer_public_key, agent_key.identifier, agent_key.address
    )
    _process_cert(agent_key, cert_request, path_prefix=data_dir)

    build_directory = build_directory or os.path.join(data_dir, "build")
    config = {"ledger_id": node_key.identifier}
    port = port or next(ports)
    configuration = ConnectionConfig(
        local_uri=f"{host}:{port}",
        entry_peers=entry_peers,
        log_file=log_file,
        peer_registration_delay=peer_registration_delay,
        connection_id=P2PLibp2pConnection.connection_id,
        build_directory=build_directory,
        cert_requests=[cert_request],
        **config,  # type: ignore
    )

    if relay:
        configuration.config["public_uri"] = f"{host}:{port}"
    if delegate:
        delegate_port = delegate_port or next(ports)
        configuration.config["delegate_uri"] = f"{delegate_host}:{delegate_port}"
    if mailbox:
        mailbox_port = mailbox_port or next(ports)
        configuration.config["mailbox_uri"] = f"{mailbox_host}:{mailbox_port}"

    if not os.path.exists(os.path.join(build_directory, LIBP2P_NODE_MODULE_NAME)):
        build_node(build_directory)

    connection = P2PLibp2pConnection(
        configuration=configuration,
        data_dir=data_dir,
        identity=identity,
        crypto_store=conn_crypto_store,
    )

    return connection


def _make_libp2p_client_connection(
    peer_public_key: str,
    data_dir: Optional[str] = None,
    node_port: Optional[int] = None,
    node_host: Optional[str] = DEFAULT_HOST,
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pClientConnection:
    """Get a libp2p client connection."""

    data_dir = data_dir or create_data_dir()
    node_port = node_port or next(ports)
    crypto = make_crypto(ledger_api_id)
    identity = create_identity(crypto)

    cert_request = make_cert_request(peer_public_key, ledger_api_id, crypto.address)
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    config = {"ledger_id": crypto.identifier}
    node = {"uri": uri or f"{node_host}:{node_port}", "public_key": peer_public_key}

    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[node],
        connection_id=P2PLibp2pClientConnection.connection_id,
        cert_requests=[cert_request],
        **config,  # type: ignore
    )

    return P2PLibp2pClientConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )


def _make_libp2p_mailbox_connection(
    peer_public_key: str,
    data_dir: Optional[str] = None,
    node_port: Optional[int] = None,
    node_host: Optional[str] = DEFAULT_HOST,
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pMailboxConnection:
    """Get a libp2p mailbox connection."""

    data_dir = data_dir or create_data_dir()
    node_port = node_port or next(ports)
    crypto = make_crypto(ledger_api_id)
    identity = create_identity(crypto)

    cert_request = make_cert_request(peer_public_key, ledger_api_id, crypto.address)
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    config = {"ledger_id": crypto.identifier}
    node = {"uri": uri or f"{node_host}:{node_port}", "public_key": peer_public_key}

    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[node],
        connection_id=P2PLibp2pMailboxConnection.connection_id,
        cert_requests=[cert_request],
        **config,  # type: ignore
    )

    return P2PLibp2pMailboxConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )


def libp2p_log_on_failure(fn: Callable) -> Callable:
    """Decorate a method running a libp2p node to print its logs in case test fails."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception:
            for log_file in getattr(self, "log_files", []):
                print(f"libp2p log file ======================= {log_file}")
                try:
                    with open(log_file, "r") as f:
                        print(f.read())
                except FileNotFoundError:
                    print("FileNotFoundError")
                print("=======================================")
            raise

    return wrapper


def libp2p_log_on_failure_all(cls: Type) -> Type:
    """Decorate every method of a class with `libp2p_log_on_failure`."""

    for name, fn in inspect.getmembers(cls, inspect.isfunction):
        setattr(cls, name, libp2p_log_on_failure(fn))

    return cls


class BaseP2PLibp2pTest:
    """Base class for ACN p2p libp2p tests"""

    cwd: str
    tmp: str
    tmp_dir: str
    tmp_client_dir: str
    log_files: List[str] = []
    multiplexers: List[Multiplexer] = []
    capture_log = True

    libp2p_crypto = cosmos_crypto = make_crypto(CosmosCrypto.identifier)
    default_crypto = ethereum_crypto = make_crypto(EthereumCrypto.identifier)
    _cryptos = (None, cosmos_crypto, ethereum_crypto)

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        atexit.register(cls.teardown_class)
        cls.cwd, cls.tmp = os.getcwd(), TEMP_LIBP2P_TEST_DIR
        if Path(cls.tmp).exists():
            cls.remove_temp_test_dir()
        Path(cls.tmp).mkdir()
        os.chdir(cls.tmp)

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        logging.debug(f"Cleaning up {cls.__name__}")
        cls._disconnect()
        cls.multiplexers.clear()
        cls.log_files.clear()
        os.chdir(cls.cwd)
        if Path(cls.tmp).exists():
            cls.remove_temp_test_dir()
        logging.debug(f"Teardown of {cls.__name__} completed")

    @classmethod
    def _disconnect(cls):
        """Disconnect multiplexers and their connections"""
        for mux in cls.multiplexers:
            mux.disconnect()
        wait_for_condition(lambda: cls.all_disconnected, timeout=TIMEOUT)

    @classmethod
    def remove_temp_test_dir(cls) -> None:
        """Attempt to remove the temporary directory used during tests"""
        success = remove_test_directory(cls.tmp)
        if not success:
            logging.debug(f"{cls.tmp} could NOT be deleted")

    def enveloped_default_message(self, to: str, sender: str) -> Envelope:
        """Generate a enveloped default message for tests"""

        message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )

        envelope = Envelope(
            to=to,
            sender=sender,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=message,
        )

        return envelope

    @property
    def _connections(self):
        return [c for m in self.multiplexers for c in m.connections]

    @property
    def all_connected(self) -> bool:
        """Check if all connection of all multiplexers are connected"""
        return all(c.is_connected for c in self._connections)

    @property
    def all_disconnected(self) -> bool:
        """Check if all connection of all multiplexers are disconnected"""
        return all(c.is_disconnected for c in self._connections)

    def sent_is_delivered_envelope(self, sent: Envelope, delivered: Envelope) -> bool:
        """Check if attributes on sent match those on delivered envelope"""
        attrs = ["to", "sender", "protocol_specification_id", "message_bytes"]
        return all(getattr(sent, attr) == getattr(delivered, attr) for attr in attrs)

    def sent_is_echoed_envelope(self, sent: Envelope, echoed: Envelope) -> bool:
        """Check if attributes on sent match those on echoed envelope"""
        attrs = ["protocol_specification_id", "message_bytes"]
        items = {"to": "sender", "sender": "to"}.items()
        attrs_are_identical = (getattr(sent, a) == getattr(echoed, a) for a in attrs)
        addresses_inverted = (getattr(sent, k) == getattr(echoed, v) for k, v in items)
        return all(attrs_are_identical) and all(addresses_inverted)

    @classmethod
    def _multiplex_it(cls, connection):
        """Create multiplexer, append it, connect it, return connection"""
        multiplexer = Multiplexer([connection], protocols=[MockDefaultMessageProtocol])
        cls.multiplexers.append(multiplexer)
        multiplexer.connect()
        wait_for_condition(lambda: connection.is_connected is True, TIMEOUT)
        return connection

    @classmethod
    def make_connection(cls, **kwargs) -> P2PLibp2pConnection:
        """Make ACN connection, auto multiplexer for teardown"""
        connection = cls._multiplex_it(_make_libp2p_connection(**kwargs))
        cls.log_files.append(connection.node.log_file)
        return connection

    @classmethod
    def make_client_connection(cls, **kwargs) -> P2PLibp2pClientConnection:
        """Make ACN client connection, auto multiplexer for teardown"""
        return cls._multiplex_it(_make_libp2p_client_connection(**kwargs))

    @classmethod
    def make_mailbox_connection(cls, **kwargs) -> P2PLibp2pMailboxConnection:
        """Make ACN mailbox connection, auto multiplexer for teardown"""
        return cls._multiplex_it(_make_libp2p_mailbox_connection(**kwargs))

    def _connections_by_type(self, cls):
        """Filter connections by type"""
        return [c for c in self._connections if isinstance(c, cls)]

    @property
    def node_connections(self) -> List[Connection]:
        """Node connections"""
        return self._connections_by_type(P2PLibp2pConnection)

    @property
    def client_connections(self) -> List[Connection]:
        """Client connections"""
        return self._connections_by_type(P2PLibp2pClientConnection)

    @property
    def mailbox_connections(self) -> List[Connection]:
        """Mailbox connections"""
        return self._connections_by_type(P2PLibp2pMailboxConnection)

    def _multiplexers_by_connection_type(self, cls):
        """Filter multiplexers by connection type"""
        mux = self.multiplexers
        return [m for m in mux if all(isinstance(c, cls) for c in m.connections)]

    @property
    def node_multiplexers(self) -> List[Multiplexer]:
        """Node multiplexers"""
        return self._multiplexers_by_connection_type(P2PLibp2pConnection)

    @property
    def client_multiplexers(self) -> List[Multiplexer]:
        """Client multiplexers"""
        return self._multiplexers_by_connection_type(P2PLibp2pClientConnection)

    @property
    def mailbox_multiplexers(self) -> List[Multiplexer]:
        """Mailbox multiplexers"""
        return self._multiplexers_by_connection_type(P2PLibp2pMailboxConnection)

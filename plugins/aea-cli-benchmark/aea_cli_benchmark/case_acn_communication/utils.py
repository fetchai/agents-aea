# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Check amount of time for acn connection start."""
import os
from pathlib import Path
from typing import Optional, Sequence, Union
from unittest.mock import patch

from aea.configurations.base import ConnectionConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea.crypto.wallet import CryptoStore
from aea.helpers.base import CertRequest, SimpleId
from aea.helpers.multiaddr.base import MultiAddr
from aea.identity.base import Identity

from packages.valory.connections.p2p_libp2p.check_dependencies import build_node
from packages.valory.connections.p2p_libp2p.connection import (
    P2PLibp2pConnection,
    POR_DEFAULT_SERVICE_ID,
)
from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
    LIBP2P_NODE_MODULE_NAME,
)
from packages.valory.connections.p2p_libp2p_client.connection import (
    P2PLibp2pClientConnection,
)
from packages.valory.connections.p2p_libp2p_mailbox.connection import (
    P2PLibp2pMailboxConnection,
)


DEFAULT_DELEGATE_PORT = 11234
DEFAULT_MAILBOX_PORT = 8888
DEFAULT_NODE_PORT = 10234


def _process_cert(key: Crypto, cert: CertRequest, path_prefix: str):
    # must match aea/cli/issue_certificates.py:_process_certificate
    assert cert.public_key is not None
    message = cert.get_message(cert.public_key)
    signature = key.sign_message(message).encode("ascii").hex()
    Path(cert.get_absolute_save_path(path_prefix)).write_bytes(
        signature.encode("ascii")
    )


def _make_libp2p_connection(
    data_dir: str,
    port: int = DEFAULT_NODE_PORT,
    host: str = "127.0.0.1",
    relay: bool = True,
    delegate: bool = False,
    mailbox: bool = False,
    entry_peers: Optional[Sequence[MultiAddr]] = None,
    delegate_port: int = DEFAULT_DELEGATE_PORT,
    delegate_host: str = "127.0.0.1",
    mailbox_port: int = DEFAULT_MAILBOX_PORT,
    mailbox_host: str = "127.0.0.1",
    node_key_file: Optional[str] = None,
    agent_key: Optional[Crypto] = None,
    build_directory: Optional[str] = None,
    peer_registration_delay: str = "0.0",
) -> P2PLibp2pConnection:
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    log_file = os.path.join(data_dir, "libp2p_node_{}.log".format(port))
    if os.path.exists(log_file):
        os.remove(log_file)
    key = agent_key
    if key is None:
        key = make_crypto(DEFAULT_LEDGER)
    identity = Identity("identity", address=key.address, public_key=key.public_key)
    conn_crypto_store = None
    if node_key_file is not None:
        conn_crypto_store = CryptoStore({DEFAULT_LEDGER: node_key_file})
    else:
        node_key = make_crypto(DEFAULT_LEDGER)
        node_key_path = os.path.join(data_dir, f"{node_key.public_key}.txt")
        node_key.dump(node_key_path)
        conn_crypto_store = CryptoStore({DEFAULT_LEDGER: node_key_path})
    cert_request = CertRequest(
        conn_crypto_store.public_keys[DEFAULT_LEDGER],
        POR_DEFAULT_SERVICE_ID,
        key.identifier,
        LIBP2P_CERT_NOT_BEFORE,
        LIBP2P_CERT_NOT_AFTER,
        "{public_key}",
        f"./{key.address}_cert.txt",
    )
    _process_cert(key, cert_request, path_prefix=data_dir)
    if not build_directory:
        build_directory = os.getcwd()
    if relay and delegate:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            delegate_uri="{}:{}".format(delegate_host, delegate_port),
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
        )
    elif relay and not delegate:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            public_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
        )
    else:
        configuration = ConnectionConfig(
            node_key_file=node_key_file,
            local_uri="{}:{}".format(host, port),
            entry_peers=entry_peers,
            log_file=log_file,
            peer_registration_delay=peer_registration_delay,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=build_directory,
            cert_requests=[cert_request],
        )

    if mailbox:
        configuration.config["mailbox_uri"] = f"{mailbox_host}:{mailbox_port}"
    else:
        configuration.config["mailbox_uri"] = ""

    if not os.path.exists(os.path.join(build_directory, LIBP2P_NODE_MODULE_NAME)):
        with patch("builtins.print"):
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
    data_dir: str,
    node_port: int = DEFAULT_DELEGATE_PORT,
    node_host: str = "127.0.0.1",
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pClientConnection:
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    crypto = make_crypto(ledger_api_id)
    identity = Identity(
        "identity", address=crypto.address, public_key=crypto.public_key
    )
    cert_request = CertRequest(
        peer_public_key,
        POR_DEFAULT_SERVICE_ID,
        ledger_api_id,
        LIBP2P_CERT_NOT_BEFORE,
        LIBP2P_CERT_NOT_AFTER,
        "{public_key}",
        f"./{crypto.address}_cert.txt",
    )
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[
            {
                "uri": str(uri)
                if uri is not None
                else "{}:{}".format(node_host, node_port),
                "public_key": peer_public_key,
            },
        ],
        connection_id=P2PLibp2pClientConnection.connection_id,
        cert_requests=[cert_request],
    )
    return P2PLibp2pClientConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )


def _make_libp2p_mailbox_connection(
    peer_public_key: str,
    data_dir: str,
    node_port: int = DEFAULT_MAILBOX_PORT,
    node_host: str = "127.0.0.1",
    uri: Optional[str] = None,
    ledger_api_id: Union[SimpleId, str] = DEFAULT_LEDGER,
) -> P2PLibp2pMailboxConnection:
    if not os.path.isdir(data_dir) or not os.path.exists(data_dir):
        raise ValueError("Data dir must be directory and exist!")
    crypto = make_crypto(ledger_api_id)
    identity = Identity(
        "identity", address=crypto.address, public_key=crypto.public_key
    )
    cert_request = CertRequest(
        peer_public_key,
        POR_DEFAULT_SERVICE_ID,
        ledger_api_id,
        LIBP2P_CERT_NOT_BEFORE,
        LIBP2P_CERT_NOT_AFTER,
        "{public_key}",
        f"./{crypto.address}_cert.txt",
    )
    _process_cert(crypto, cert_request, path_prefix=data_dir)
    configuration = ConnectionConfig(
        tcp_key_file=None,
        nodes=[
            {
                "uri": str(uri)
                if uri is not None
                else "{}:{}".format(node_host, node_port),
                "public_key": peer_public_key,
            },
        ],
        connection_id=P2PLibp2pMailboxConnection.connection_id,
        cert_requests=[cert_request],
    )
    return P2PLibp2pMailboxConnection(
        configuration=configuration, data_dir=data_dir, identity=identity
    )

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
"""This test module contains negative tests for Libp2p tcp client connection."""
import asyncio
import os
import shutil
import tempfile
from asyncio.futures import Future
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import ConnectionConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.helpers.base import CertRequest
from aea.identity.base import Identity
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p_client.connection import (
    POR_DEFAULT_SERVICE_ID,
)
from packages.fetchai.connections.p2p_libp2p_mailbox.connection import (
    P2PLibp2pMailboxConnection,
)

from tests.conftest import (
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    _make_libp2p_mailbox_connection,
    _process_cert,
    libp2p_log_on_failure,
)


@pytest.mark.asyncio
class TestLibp2pClientConnectionFailureNodeNotConnected:
    """Test that connection fails when node not running"""

    @pytest.mark.asyncio
    async def test_node_not_running(self):
        """Test the node is not running."""
        with tempfile.TemporaryDirectory() as dirname:
            conn = _make_libp2p_mailbox_connection(
                data_dir=dirname, peer_public_key=make_crypto(DEFAULT_LEDGER).public_key
            )
            with pytest.raises(Exception):
                await conn.connect()


class TestLibp2pClientConnectionFailureConnectionSetup:
    """Test that connection fails when setup incorrectly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        crypto = make_crypto(DEFAULT_LEDGER)
        cls.node_host = "localhost"
        cls.node_port = "11234"
        cls.identity = Identity(
            "identity", address=crypto.address, public_key=crypto.public_key
        )

        cls.key_file = os.path.join(cls.t, "keyfile")
        crypto.dump(cls.key_file)

        cls.peer_crypto = make_crypto(DEFAULT_LEDGER)
        cls.cert_request = CertRequest(
            cls.peer_crypto.public_key,
            POR_DEFAULT_SERVICE_ID,
            DEFAULT_LEDGER,
            "2021-01-01",
            "2021-01-02",
            "{public_key}",
            f"./{crypto.address}_cert.txt",
        )
        _process_cert(crypto, cls.cert_request, cls.t)

    def test_empty_nodes(self):
        """Test empty nodes."""
        configuration = ConnectionConfig(
            tcp_key_file=self.key_file,
            nodes=[
                {
                    "uri": "{}:{}".format(self.node_host, self.node_port),
                    "public_key": self.peer_crypto.public_key,
                }
            ],
            connection_id=P2PLibp2pMailboxConnection.connection_id,
            cert_requests=[self.cert_request],
        )
        P2PLibp2pMailboxConnection(
            configuration=configuration, data_dir=self.t, identity=self.identity
        )

        configuration = ConnectionConfig(
            tcp_key_file=self.key_file,
            nodes=None,
            connection_id=P2PLibp2pMailboxConnection.connection_id,
        )
        with pytest.raises(Exception):
            P2PLibp2pMailboxConnection(
                configuration=configuration, data_dir=self.t, identity=self.identity,
            )

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestLibp2pClientConnectionNodeDisconnected:
    """Test that connection will properly handle node disconnecting"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []
        cls.multiplexers = []

        temp_node_dir = os.path.join(cls.t, "node_dir")
        os.mkdir(temp_node_dir)
        try:
            cls.connection_node = _make_libp2p_connection(
                data_dir=temp_node_dir, delegate=True
            )
            cls.multiplexer_node = Multiplexer([cls.connection_node])
            cls.log_files.append(cls.connection_node.node.log_file)
            cls.multiplexer_node.connect()
            cls.multiplexers.append(cls.multiplexer_node)

            temp_client_dir = os.path.join(cls.t, "client_dir")
            os.mkdir(temp_client_dir)
            cls.connection_client = _make_libp2p_client_connection(
                data_dir=temp_client_dir, peer_public_key=cls.connection_node.node.pub
            )
            cls.multiplexer_client = Multiplexer([cls.connection_client])
            cls.multiplexer_client.connect()
            cls.multiplexers.append(cls.multiplexer_client)
        except Exception:
            cls.teardown_class()
            raise

    def test_node_disconnected(self):
        """Test node disconnected."""
        assert self.connection_client.is_connected is True
        self.multiplexer_client.disconnect()
        self.multiplexer_node.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        for mux in cls.multiplexers:
            mux.disconnect()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


done_future: asyncio.Future = asyncio.Future()
done_future.set_result(None)


@pytest.mark.asyncio
async def test_connect_attempts():
    """Test connect attempts."""
    # test connects
    with tempfile.TemporaryDirectory() as dirname:
        con = _make_libp2p_client_connection(
            data_dir=dirname, peer_public_key=make_crypto(DEFAULT_LEDGER).public_key
        )
        con.connect_retries = 2
        with patch(
            "aea.helpers.pipe.TCPSocketChannelClient.connect",
            side_effect=Exception("test exception on connect"),
        ) as open_connection_mock:
            with pytest.raises(Exception, match="test exception on connect"):
                await con.connect()
            assert open_connection_mock.call_count == con.connect_retries


@pytest.mark.asyncio
async def test_reconnect_on_receive_fail():
    """Test reconnect on receive fails."""
    with tempfile.TemporaryDirectory() as dirname:
        con = _make_libp2p_mailbox_connection(
            data_dir=dirname, peer_public_key=make_crypto(DEFAULT_LEDGER).public_key
        )
        con._in_queue = Mock()
        con._node_client = Mock()
        f = Future()
        f.set_exception(ConnectionError("oops"))
        con._node_client.read_envelope.return_value = f

        with patch.object(
            con, "_perform_connection_to_node", return_value=done_future
        ) as connect_mock:
            assert await con._read_envelope_from_node() is None
            connect_mock.assert_called()


@pytest.mark.asyncio
async def test_reconnect_on_send_fail():
    """Test reconnect on send fails."""
    with tempfile.TemporaryDirectory() as dirname:
        con = _make_libp2p_mailbox_connection(
            data_dir=dirname, peer_public_key=make_crypto(DEFAULT_LEDGER).public_key
        )
        con._node_client = Mock()
        f = Future()
        f.set_exception(Exception("oops"))
        con._node_client.send_envelope.side_effect = Exception("oops")
        # test reconnect on send fails
        with patch.object(
            con, "_perform_connection_to_node", return_value=done_future
        ) as connect_mock, patch.object(
            con, "_ensure_valid_envelope_for_external_comms"
        ):
            with pytest.raises(Exception, match="oops"):
                await con._send_envelope_with_node_client(Mock())
            connect_mock.assert_called()

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

import os
import shutil
import tempfile

import pytest

from aea.configurations.base import ConnectionConfig
from aea.crypto.registries import make_crypto
from aea.identity.base import Identity
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p_client.connection import (
    P2PLibp2pClientConnection,
)

from tests.conftest import (
    COSMOS,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
)


@pytest.mark.asyncio
class TestLibp2pClientConnectionFailureNodeNotConnected:
    """Test that connection fails when node not running"""

    @pytest.mark.asyncio
    async def test_node_not_running(self):
        """Test the node is not running."""
        conn = _make_libp2p_client_connection()
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
        crypto = make_crypto(COSMOS)
        cls.node_host = "localhost"
        cls.node_port = "11234"
        cls.identity = Identity("", address=crypto.address)

        cls.key_file = os.path.join(cls.t, "keyfile")
        key_file_desc = open(cls.key_file, "ab")
        crypto.dump(key_file_desc)
        key_file_desc.close()

    def test_empty_nodes(self):
        """Test empty nodes."""
        configuration = ConnectionConfig(
            client_key_file=self.key_file,
            nodes=[{"uri": "{}:{}".format(self.node_host, self.node_port)}],
            connection_id=P2PLibp2pClientConnection.connection_id,
        )
        P2PLibp2pClientConnection(configuration=configuration, identity=self.identity)

        configuration = ConnectionConfig(
            client_key_file=self.key_file,
            nodes=None,
            connection_id=P2PLibp2pClientConnection.connection_id,
        )
        with pytest.raises(Exception):
            P2PLibp2pClientConnection(
                configuration=configuration, identity=self.identity
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

        try:
            cls.connection_node = _make_libp2p_connection(delegate=True)
            cls.multiplexer_node = Multiplexer([cls.connection_node])
            cls.log_files.append(cls.connection_node.node.log_file)
            cls.multiplexer_node.connect()
            cls.multiplexers.append(cls.multiplexer_node)

            cls.connection_client = _make_libp2p_client_connection()
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

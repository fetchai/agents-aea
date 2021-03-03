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
"""This test module contains Negative tests for Libp2p connection."""
import os
import shutil
import tempfile
from asyncio.futures import Future
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import ConnectionConfig
from aea.crypto.registries import make_crypto
from aea.identity.base import Identity
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p.connection import (
    LIBP2P_NODE_MODULE_NAME,
    Libp2pNode,
    P2PLibp2pConnection,
    _golang_module_run,
    _ip_all_private_or_all_public,
)

from tests.conftest import DEFAULT_LEDGER, _make_libp2p_connection


DEFAULT_PORT = 10234
DEFAULT_NET_SIZE = 4


class TestP2PLibp2pConnectionFailureGolangRun:
    """Test that golang run fails if wrong path or timeout"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        temp_dir = os.path.join(cls.t, "temp_dir")
        os.mkdir(temp_dir)
        cls.connection = _make_libp2p_connection(data_dir=temp_dir)
        cls.wrong_path = tempfile.mkdtemp()

    def test_wrong_path(self):
        """Test the wrong path."""
        log_file_desc = open("log", "a", 1)
        with pytest.raises(Exception):
            _golang_module_run(
                self.wrong_path, LIBP2P_NODE_MODULE_NAME, [], log_file_desc
            )

    def test_timeout(self):
        """Test the timeout."""
        self.connection.node._connection_timeout = 0
        muxer = Multiplexer([self.connection])
        with pytest.raises(Exception):
            muxer.connect()
        muxer.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
            shutil.rmtree(cls.wrong_path)
        except (OSError, IOError):
            pass


class TestP2PLibp2pConnectionFailureNodeDisconnect:
    """Test that connection handles node disconnecting properly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        temp_dir = os.path.join(cls.t, "temp_dir")
        os.mkdir(temp_dir)
        cls.connection = _make_libp2p_connection(data_dir=temp_dir)

    def test_node_disconnect(self):
        """Test node disconnect."""
        muxer = Multiplexer([self.connection])
        muxer.connect()
        self.connection.node.proc.terminate()
        self.connection.node.proc.wait()
        muxer.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestP2PLibp2pConnectionFailureSetupNewConnection:
    """Test that connection constructor ensures proper configuration"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        crypto = make_crypto(DEFAULT_LEDGER)
        cls.identity = Identity("", address=crypto.address)
        cls.host = "localhost"
        cls.port = "10000"

        cls.key_file = os.path.join(cls.t, "keyfile")
        key_file_desc = open(cls.key_file, "ab")
        crypto.dump(key_file_desc)
        key_file_desc.close()

    def test_entry_peers_when_no_public_uri_provided(self):
        """Test entry peers when no public uri provided."""
        configuration = ConnectionConfig(
            libp2p_key_file=None,
            local_uri="{}:{}".format(self.host, self.port),
            delegate_uri="{}:{}".format(self.host, self.port),
            entry_peers=None,
            log_file=None,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=self.t,
        )
        with pytest.raises(ValueError):
            P2PLibp2pConnection(
                configuration=configuration, data_dir=self.t, identity=self.identity
            )

    def test_local_uri_provided_when_public_uri_provided(self):
        """Test local uri provided when public uri provided."""
        configuration = ConnectionConfig(
            node_key_file=self.key_file,
            public_uri="{}:{}".format(self.host, self.port),
            entry_peers=None,
            log_file=None,
            connection_id=P2PLibp2pConnection.connection_id,
            build_directory=self.t,
        )
        with pytest.raises(ValueError):
            P2PLibp2pConnection(
                configuration=configuration, data_dir=self.t, identity=self.identity
            )

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


def test_libp2pconnection_mixed_ip_address():
    """Test correct public uri ip and entry peers ips configuration."""
    assert _ip_all_private_or_all_public([]) is True
    assert _ip_all_private_or_all_public(["127.0.0.1", "127.0.0.1"]) is True
    assert _ip_all_private_or_all_public(["localhost", "127.0.0.1"]) is True
    assert _ip_all_private_or_all_public(["10.0.0.1", "127.0.0.1"]) is False
    assert _ip_all_private_or_all_public(["fetch.ai", "127.0.0.1"]) is False
    assert _ip_all_private_or_all_public(["104.26.2.97", "127.0.0.1"]) is False
    assert _ip_all_private_or_all_public(["fetch.ai", "acn.fetch.ai"]) is True


def test_libp2pconnection_node_config_registration_delay():
    """Test node registration delay configuration"""
    host = "localhost"
    port = "10000"

    with tempfile.TemporaryDirectory() as data_dir:
        _make_libp2p_connection(
            port=port, host=host, data_dir=data_dir, build_directory=data_dir
        )
    with tempfile.TemporaryDirectory() as data_dir:
        with pytest.raises(ValueError):
            _make_libp2p_connection(
                port=port,
                host=host,
                data_dir=data_dir,
                peer_registration_delay="must_be_float",
                build_directory=data_dir,
            )


def test_build_dir_not_set():
    """Test build dir not set."""
    host = "localhost"
    port = "10000"
    with tempfile.TemporaryDirectory() as data_dir:
        con = _make_libp2p_connection(
            port=port, host=host, data_dir=data_dir, build_directory=data_dir
        )
        con.configuration.build_directory = None
        with pytest.raises(
            ValueError, match="Connection Configuration build directory is not set!"
        ):
            P2PLibp2pConnection(
                configuration=con.configuration,
                data_dir=data_dir,
                identity=con._identity,
                crypto_store=con.crypto_store,
            )


@pytest.mark.asyncio
async def test_reconnect_on_write_failed():
    """Test node restart on write fail."""
    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    node.pipe = Mock()
    node.pipe.write = Mock(side_effect=Exception("expected"))
    f = Future()
    f.set_result(None)
    with patch.object(node, "restart", return_value=f) as restart_mock, pytest.raises(
        Exception, match="expected"
    ):
        await node.write(b"some_data")

    assert node.pipe.write.call_count == 2
    restart_mock.assert_called_once()


@pytest.mark.asyncio
async def test_reconnect_on_read_failed():
    """Test node restart on read fail."""
    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp")
    node.pipe = Mock()
    node.pipe.read = Mock(side_effect=Exception("expected"))
    f = Future()
    f.set_result(None)
    with patch.object(node, "restart", return_value=f) as restart_mock:
        result = await node.read()

    assert result is None

    assert node.pipe.read.call_count == 2
    restart_mock.assert_called_once()


@pytest.mark.asyncio
async def test_max_restarts():
    """Test node max restarts exception."""
    node = Libp2pNode(Mock(), Mock(), "tmp", "tmp", max_restarts=0)
    with pytest.raises(ValueError, match="Max restarts attempts reached:"):
        await node.restart()

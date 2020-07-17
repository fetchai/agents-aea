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

import asyncio
import os
import shutil
import tempfile

import pytest

from aea.configurations.base import ConnectionConfig
from aea.crypto.registries import make_crypto
from aea.identity.base import Identity
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.p2p_libp2p.connection import (
    AwaitableProc,
    LIBP2P_NODE_MODULE_NAME,
    P2PLibp2pConnection,
    _golang_module_build_async,
    _golang_module_run,
)

from tests.conftest import (
    COSMOS,
    _make_libp2p_connection,
    skip_test_windows,
)

DEFAULT_PORT = 10234
DEFAULT_NET_SIZE = 4


@skip_test_windows
@pytest.mark.asyncio
class TestP2PLibp2pConnectionFailureGolangBuild:
    """Test that golang build async fails if timeout exceeded or wrong path"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.connection = _make_libp2p_connection()
        cls.wrong_path = tempfile.mkdtemp()

    @pytest.mark.asyncio
    async def test_timeout(self):
        log_file_desc = open("log", "a", 1)
        with pytest.raises(Exception):
            await _golang_module_build_async(
                self.connection.node.source, log_file_desc, timeout=0
            )

    @pytest.mark.asyncio
    async def test_wrong_path(self):
        self.connection.node.source = self.wrong_path
        with pytest.raises(Exception):
            await self.connection.connect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
            shutil.rmtree(cls.wrong_path)
        except (OSError, IOError):
            pass


@skip_test_windows
class TestP2PLibp2pConnectionFailureGolangRun:
    """Test that golang run fails if wrong path or timeout"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.connection = _make_libp2p_connection()
        cls.wrong_path = tempfile.mkdtemp()

    def test_wrong_path(self):
        log_file_desc = open("log", "a", 1)
        with pytest.raises(Exception):
            _golang_module_run(
                self.wrong_path, LIBP2P_NODE_MODULE_NAME, [], log_file_desc
            )

    def test_timeout(self):
        self.connection.node._connection_timeout = 0
        self.connection.node._connection_attempts = 2
        with pytest.raises(Exception):
            muxer = Multiplexer([self.connection])
            muxer.connect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
            shutil.rmtree(cls.wrong_path)
        except (OSError, IOError):
            pass


@skip_test_windows
class TestP2PLibp2pConnectionFailureNodeDisconnect:
    """Test that connection handles node disconnecting properly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.connection = _make_libp2p_connection()

    def test_node_disconnect(self):
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


@skip_test_windows
class TestP2PLibp2pConnectionFailureSetupNewConnection:
    """Test that connection constructor ensures proper configuration"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        crypto = make_crypto(COSMOS)
        cls.identity = Identity("", address=crypto.address)
        cls.host = "localhost"
        cls.port = "10000"

        cls.key_file = os.path.join(cls.t, "keyfile")
        key_file_desc = open(cls.key_file, "ab")
        crypto.dump(key_file_desc)
        key_file_desc.close()

    def test_entry_peers_when_no_public_uri_provided(self):
        configuration = ConnectionConfig(
            libp2p_key_file=None,
            local_uri="{}:{}".format(self.host, self.port),
            delegate_uri="{}:{}".format(self.host, self.port),
            entry_peers=None,
            log_file=None,
            connection_id=P2PLibp2pConnection.connection_id,
        )
        with pytest.raises(ValueError):
            P2PLibp2pConnection(configuration=configuration, identity=self.identity)

    def test_local_uri_provided_when_public_uri_provided(self):

        configuration = ConnectionConfig(
            node_key_file=self.key_file,
            public_uri="{}:{}".format(self.host, self.port),
            entry_peers=None,
            log_file=None,
            connection_id=P2PLibp2pConnection.connection_id,
        )
        with pytest.raises(ValueError):
            P2PLibp2pConnection(configuration=configuration, identity=self.identity)

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@skip_test_windows
def test_libp2pconnection_awaitable_proc_cancelled():
    proc = AwaitableProc(["sleep", "100"], shell=False)
    proc_task = asyncio.ensure_future(proc.start())
    proc_task.cancel()

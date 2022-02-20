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
"""This test module contains tests for P2PLibp2p connection."""
import os
import shutil
import tempfile
from unittest.mock import Mock

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.common.utils import wait_for_condition
from tests.conftest import (
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234

MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@libp2p_log_on_failure_all
class TestSlowQueue:
    """Test that libp2p node uses slow queue in case of long DHT lookups."""

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
            port_genesis = DEFAULT_PORT + 10
            temp_dir_gen = os.path.join(cls.t, "temp_dir_gen")
            os.mkdir(temp_dir_gen)
            cls.bad_address = _make_libp2p_connection(
                data_dir=temp_dir_gen, port=port_genesis
            ).node.address
            cls.connection_genesis = _make_libp2p_connection(
                data_dir=temp_dir_gen, port=port_genesis
            )
            cls.multiplexer_genesis = Multiplexer(
                [cls.connection_genesis], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.connection_genesis.node.multiaddrs[0]

            cls.connections = [cls.connection_genesis]

            temp_dir = os.path.join(cls.t, "temp_dir_100")
            os.mkdir(temp_dir)

            cls.conn = _make_libp2p_connection(
                data_dir=temp_dir, port=port_genesis + 100, entry_peers=[genesis_peer]
            )

            port = port_genesis
            for i in range(2):
                port += 1
                temp_dir = os.path.join(cls.t, f"temp_dir_{i}")
                os.mkdir(temp_dir)
                conn = _make_libp2p_connection(
                    data_dir=temp_dir, port=port, entry_peers=[genesis_peer]
                )
                mux = Multiplexer([conn], protocols=[MockDefaultMessageProtocol])

                cls.connections.append(conn)

                cls.log_files.append(conn.node.log_file)
                mux.connect()
                cls.multiplexers.append(mux)

            for conn in cls.connections:
                assert conn.is_connected is True
        except Exception as e:
            cls.teardown_class()
            raise e

    @pytest.mark.asyncio
    async def test_slow_queue(self):
        """Test slow queue."""
        con2 = self.connections[-1]
        await self.conn.connect()

        def _make_envelope(addr):
            msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"hello",
            )

            envelope = Envelope(to=addr, sender=self.conn.node.address, message=msg,)
            return envelope

        try:
            for _ in range(50):
                for addr in [con2.node.address, self.bad_address]:
                    await self.conn._node_client.send_envelope(_make_envelope(addr))

            for _ in range(2):
                for addr in [self.bad_address, con2.node.address]:
                    await self.conn._node_client.send_envelope(_make_envelope(addr))

            def _check():
                with open(self.conn.node.log_file) as f:
                    return "while sending slow envelope:" in f.read()

            wait_for_condition(_check, timeout=30, period=1)
        finally:
            await self.conn.disconnect()

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

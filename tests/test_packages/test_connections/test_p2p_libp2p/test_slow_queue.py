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

from unittest.mock import Mock

import pytest

from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.common.utils import wait_for_condition
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
)


MockDefaultMessageProtocol = Mock()
MockDefaultMessageProtocol.protocol_id = DefaultMessage.protocol_id
MockDefaultMessageProtocol.protocol_specification_id = (
    DefaultMessage.protocol_specification_id
)


@libp2p_log_on_failure_all
class TestSlowQueue(BaseP2PLibp2pTest):
    """Test that libp2p node uses slow queue in case of long DHT lookups."""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        super().setup_class()

        try:
            cls.bad_address = _make_libp2p_connection().address
            cls.connection_genesis = _make_libp2p_connection()
            cls.multiplexer_genesis = Multiplexer(
                [cls.connection_genesis], protocols=[MockDefaultMessageProtocol]
            )
            cls.log_files.append(cls.connection_genesis.node.log_file)
            cls.multiplexer_genesis.connect()
            cls.multiplexers.append(cls.multiplexer_genesis)

            genesis_peer = cls.connection_genesis.node.multiaddrs[0]

            cls.connections = [cls.connection_genesis]
            cls.conn = _make_libp2p_connection(entry_peers=[genesis_peer])

            for _ in range(2):
                conn = _make_libp2p_connection(entry_peers=[genesis_peer])
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

        try:
            for _ in range(50):
                for addr in [con2.address, self.bad_address]:
                    sender = self.conn.address
                    envelope = self.enveloped_default_message(addr, sender)
                    await self.conn._node_client.send_envelope(envelope)

            for _ in range(2):
                for addr in [self.bad_address, con2.address]:
                    sender = self.conn.address
                    envelope = self.enveloped_default_message(addr, sender)
                    await self.conn._node_client.send_envelope(envelope)

            def _check():
                with open(self.conn.node.log_file) as f:
                    return "while sending slow envelope:" in f.read()

            wait_for_condition(_check, timeout=30, period=1)
        finally:
            await self.conn.disconnect()

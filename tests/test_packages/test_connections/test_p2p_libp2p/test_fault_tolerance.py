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

"""This test module contains resilience and fault tolerance tests for P2PLibp2p connection."""

import os
import shutil
import tempfile
import time

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.registries import make_crypto
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from tests.conftest import (
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)

DEFAULT_PORT = 10234


@libp2p_log_on_failure_all
class TestLibp2pConnectionRelayNodeRestart:
    """Test that connection will reliably route envelope to destination in case of relay node restart within timeout"""

    @classmethod
    @libp2p_log_on_failure
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

        cls.genesis = _make_libp2p_connection(DEFAULT_PORT + 1)

        cls.multiplexer_genesis = Multiplexer([cls.genesis])
        cls.log_files.append(cls.genesis.node.log_file)
        cls.multiplexer_genesis.connect()

        genesis_peer = cls.genesis.node.multiaddrs[0]

        with open("node_key", "wb") as f:
            make_crypto(DEFAULT_LEDGER).dump(f)
            cls.relay_key_path = "node_key"

        cls.relay = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            entry_peers=[genesis_peer],
            node_key_file=cls.relay_key_path,
        )
        cls.multiplexer_relay = Multiplexer([cls.relay])
        cls.log_files.append(cls.relay.node.log_file)
        cls.multiplexer_relay.connect()

        relay_peer = cls.relay.node.multiaddrs[0]

        cls.connection = _make_libp2p_connection(
            DEFAULT_PORT + 3, relay=False, entry_peers=[relay_peer]
        )
        cls.multiplexer = Multiplexer([cls.connection])
        cls.log_files.append(cls.connection.node.log_file)
        cls.multiplexer.connect()

    def test_connection_is_established(self):
        assert self.relay.is_connected is True
        assert self.connection.is_connected is True

    def test_envelope_routed_after_relay_restart(self):
        addr_1 = self.connection.address
        addr_2 = self.genesis.address

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer.put(envelope)
        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message_bytes == envelope.message_bytes

        self.multiplexer_relay.disconnect()

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"helloAfterRestart",
        )
        envelope = Envelope(
            to=addr_2,
            sender=addr_1,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(msg),
        )

        self.multiplexer.put(envelope)
        time.sleep(5)

        TestLibp2pConnectionRelayNodeRestart.relay = _make_libp2p_connection(
            port=DEFAULT_PORT + 2,
            entry_peers=[self.genesis.node.multiaddrs[0]],
            node_key_file=self.relay_key_path,
        )
        TestLibp2pConnectionRelayNodeRestart.multiplexer_relay = Multiplexer(
            [self.relay]
        )
        self.multiplexer_relay.connect()

        delivered_envelope = self.multiplexer_genesis.get(block=True, timeout=20)

        assert delivered_envelope is not None
        assert delivered_envelope.to == envelope.to
        assert delivered_envelope.sender == envelope.sender
        assert delivered_envelope.protocol_id == envelope.protocol_id
        assert delivered_envelope.message_bytes == envelope.message_bytes

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.multiplexer.disconnect()
        cls.multiplexer_relay.disconnect()
        cls.multiplexer_genesis.disconnect()

        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

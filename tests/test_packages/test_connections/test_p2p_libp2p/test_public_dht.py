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

"""This test module contains integration tests for P2PLibp2p connection."""

import os
import shutil
import tempfile

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.fetchai.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.connections.p2p_libp2p_client.connection import (
    PUBLIC_ID as P2P_CLIENT_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import (
    PUBLIC_DHT_DELEGATE_URI_1,
    PUBLIC_DHT_DELEGATE_URI_2,
    PUBLIC_DHT_P2P_MADDR_1,
    PUBLIC_DHT_P2P_MADDR_2,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234
PUBLIC_DHT_MADDRS = [PUBLIC_DHT_P2P_MADDR_1, PUBLIC_DHT_P2P_MADDR_2]
PUBLIC_DHT_DELEGATE_URIS = [PUBLIC_DHT_DELEGATE_URI_1, PUBLIC_DHT_DELEGATE_URI_2]
AEA_DEFAULT_LAUNCH_TIMEOUT = 15
AEA_LIBP2P_LAUNCH_TIMEOUT = 660  # may download up to ~66Mb


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTRelay:
    """Test that public DHT's relay service is working properly"""

    @classmethod
    def setup_class(cls):
        """Set the test up"""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.log_files = []

    def test_connectivity(self):
        """Test connectivity."""
        for maddr in PUBLIC_DHT_MADDRS:
            connection = _make_libp2p_connection(
                DEFAULT_PORT + 1, relay=False, entry_peers=[maddr]
            )
            multiplexer = Multiplexer([connection])
            self.log_files.append(connection.node.log_file)
            multiplexer.connect()

            try:
                assert (
                    connection.is_connected is True
                ), "Couldn't connect to public node {}".format(maddr)
            except Exception:
                raise
            finally:
                multiplexer.disconnect()

    def test_communication_direct(self):
        """Test communication direct."""
        for maddr in PUBLIC_DHT_MADDRS:
            multiplexers = []
            try:
                connection1 = _make_libp2p_connection(
                    DEFAULT_PORT + 1, relay=False, entry_peers=[maddr]
                )
                multiplexer1 = Multiplexer([connection1])
                self.log_files.append(connection1.node.log_file)
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                connection2 = _make_libp2p_connection(
                    DEFAULT_PORT + 2, relay=False, entry_peers=[maddr]
                )
                multiplexer2 = Multiplexer([connection2])
                self.log_files.append(connection2.node.log_file)
                multiplexer2.connect()
                multiplexers.append(multiplexer2)

                addr_1 = connection1.node.address
                addr_2 = connection2.node.address

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
                    message=msg,
                )

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                msg.to = delivered_envelope.to
                msg.sender = delivered_envelope.sender
                assert envelope.message == msg
            except Exception:
                raise
            finally:
                for mux in multiplexers:
                    mux.disconnect()

    def test_communication_indirect(self):
        """Test communication indirect."""
        assert len(PUBLIC_DHT_MADDRS) > 1, "Test requires at least 2 public dht node"

        for i in range(len(PUBLIC_DHT_MADDRS)):
            multiplexers = []
            try:
                connection1 = _make_libp2p_connection(
                    DEFAULT_PORT + 1, relay=False, entry_peers=[PUBLIC_DHT_MADDRS[i]]
                )
                multiplexer1 = Multiplexer([connection1])
                self.log_files.append(connection1.node.log_file)
                multiplexer1.connect()
                multiplexers.append(multiplexer1)
                addr_1 = connection1.node.address

                for j in range(len(PUBLIC_DHT_MADDRS)):
                    if j == i:
                        continue

                    connection2 = _make_libp2p_connection(
                        DEFAULT_PORT + 2,
                        relay=False,
                        entry_peers=[PUBLIC_DHT_MADDRS[j]],
                    )
                    multiplexer2 = Multiplexer([connection2])
                    self.log_files.append(connection2.node.log_file)
                    multiplexer2.connect()
                    multiplexers.append(multiplexer2)

                    addr_2 = connection2.node.address

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
                        message=msg,
                    )

                    multiplexer1.put(envelope)
                    delivered_envelope = multiplexer2.get(block=True, timeout=20)

                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert delivered_envelope.protocol_id == envelope.protocol_id
                    assert delivered_envelope.message != envelope.message
                    msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                    msg.to = delivered_envelope.to
                    msg.sender = delivered_envelope.sender
                    assert envelope.message == msg
                    multiplexer2.disconnect()
                    del multiplexers[-1]
            except Exception:
                raise
            finally:
                for mux in multiplexers:
                    mux.disconnect()

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegate:
    """Test that public DHT's delegate service is working properly"""

    def test_connectivity(self):
        """Test connectivity."""
        for uri in PUBLIC_DHT_DELEGATE_URIS:
            connection = _make_libp2p_client_connection(uri=uri)
            multiplexer = Multiplexer([connection])

            try:
                multiplexer.connect()
                assert (
                    connection.is_connected is True
                ), "Couldn't connect to public node {}".format(uri)
            except Exception:
                raise
            finally:
                multiplexer.disconnect()

    def test_communication_direct(self):
        """Test communication direct."""
        for uri in PUBLIC_DHT_DELEGATE_URIS:
            multiplexers = []
            try:
                connection1 = _make_libp2p_client_connection(uri=uri)
                multiplexer1 = Multiplexer([connection1])
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                connection2 = _make_libp2p_client_connection(uri=uri)
                multiplexer2 = Multiplexer([connection2])
                multiplexer2.connect()
                multiplexers.append(multiplexer2)

                addr_1 = connection1.address
                addr_2 = connection2.address

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
                    message=msg,
                )

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert delivered_envelope.protocol_id == envelope.protocol_id
                assert delivered_envelope.message != envelope.message
                msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                msg.to = delivered_envelope.to
                msg.sender = delivered_envelope.sender
                assert envelope.message == msg
            except Exception:
                raise
            finally:
                for mux in multiplexers:
                    mux.disconnect()

    def test_communication_indirect(self):
        """Test communication indirect."""
        assert (
            len(PUBLIC_DHT_DELEGATE_URIS) > 1
        ), "Test requires at least 2 public dht node"

        for i in range(len(PUBLIC_DHT_DELEGATE_URIS)):
            multiplexers = []
            try:
                connection1 = _make_libp2p_client_connection(
                    uri=PUBLIC_DHT_DELEGATE_URIS[i]
                )
                multiplexer1 = Multiplexer([connection1])
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                addr_1 = connection1.address

                for j in range(len(PUBLIC_DHT_DELEGATE_URIS)):
                    if j == i:
                        continue

                    connection2 = _make_libp2p_client_connection(
                        uri=PUBLIC_DHT_DELEGATE_URIS[j]
                    )
                    multiplexer2 = Multiplexer([connection2])
                    multiplexer2.connect()
                    multiplexers.append(multiplexer2)

                    addr_2 = connection2.address
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
                        message=msg,
                    )

                    multiplexer1.put(envelope)
                    delivered_envelope = multiplexer2.get(block=True, timeout=20)

                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert delivered_envelope.protocol_id == envelope.protocol_id
                    assert delivered_envelope.message != envelope.message
                    msg = DefaultMessage.serializer.decode(delivered_envelope.message)
                    msg.to = delivered_envelope.to
                    msg.sender = delivered_envelope.sender
                    assert envelope.message == msg
                    multiplexer2.disconnect()
                    del multiplexers[-1]
            except Exception:
                raise
            finally:
                for mux in multiplexers:
                    mux.disconnect()


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTRelayAEACli(AEATestCaseEmpty):
    """Test that public DHT's relay service is working properly, using aea cli"""

    @libp2p_log_on_failure
    def test_connectivity(self):
        """Test connectivity."""
        self.log_files = []
        self.add_item("connection", str(P2P_CONNECTION_PUBLIC_ID))
        self.run_cli_command("build", cwd=self._get_cwd())

        self.set_config("agent.default_connection", str(P2P_CONNECTION_PUBLIC_ID))

        # for logging
        log_file = "libp2p_node_{}.log".format(self.agent_name)
        log_file = os.path.join(os.path.abspath(os.getcwd()), log_file)

        config_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.nested_set_config(
            config_path,
            {
                "local_uri": "127.0.0.1:{}".format(DEFAULT_PORT),
                "entry_peers": PUBLIC_DHT_MADDRS,
                "log_file": log_file,
            },
        )

        self.log_files = [log_file]
        process = self.run_agent()

        is_running = self.is_running(process, timeout=AEA_LIBP2P_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "Peer running in "
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.terminate_agents()
        super(TestLibp2pConnectionPublicDHTRelayAEACli, cls).teardown_class()


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegateAEACli(AEATestCaseEmpty):
    """Test that public DHT's delegate service is working properly, using aea cli"""

    def test_connectivity(self):
        """Test connectivity."""
        self.add_item("connection", str(P2P_CLIENT_CONNECTION_PUBLIC_ID))
        config_path = "vendor.fetchai.connections.p2p_libp2p_client.config"
        self.nested_set_config(
            config_path,
            {"nodes": [{"uri": "{}".format(uri)} for uri in PUBLIC_DHT_DELEGATE_URIS]},
        )

        process = self.run_agent()
        is_running = self.is_running(process, timeout=AEA_DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.terminate_agents()
        super(TestLibp2pConnectionPublicDHTDelegateAEACli, cls).teardown_class()

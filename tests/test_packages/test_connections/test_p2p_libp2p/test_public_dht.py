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

from aea.helpers.base import CertRequest
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
    PUBLIC_DHT_P2P_PUBLIC_KEY_1,
    PUBLIC_DHT_P2P_PUBLIC_KEY_2,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure,
    libp2p_log_on_failure_all,
)


DEFAULT_PORT = 10234
PUBLIC_DHT_MADDRS = [PUBLIC_DHT_P2P_MADDR_1, PUBLIC_DHT_P2P_MADDR_2]
PUBLIC_DHT_DELEGATE_URIS = [PUBLIC_DHT_DELEGATE_URI_1, PUBLIC_DHT_DELEGATE_URI_2]
PUBLIC_DHT_PUBLIC_KEYS = [PUBLIC_DHT_P2P_PUBLIC_KEY_1, PUBLIC_DHT_P2P_PUBLIC_KEY_2]
AEA_DEFAULT_LAUNCH_TIMEOUT = 20
AEA_LIBP2P_LAUNCH_TIMEOUT = 20


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTRelay:
    """Test that public DHT's relay service is working properly"""

    def setup(self):
        """Set the test up"""
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        os.chdir(self.t)

        self.log_files = []

    def test_connectivity(self):
        """Test connectivity."""
        for i, maddr in enumerate(PUBLIC_DHT_MADDRS):
            temp_dir = os.path.join(self.t, f"dir_{i}")
            os.mkdir(temp_dir)
            connection = _make_libp2p_connection(
                port=DEFAULT_PORT + 1,
                relay=False,
                entry_peers=[maddr],
                data_dir=temp_dir,
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
        for i, maddr in enumerate(PUBLIC_DHT_MADDRS):
            multiplexers = []
            try:
                temp_dir_1 = os.path.join(self.t, f"dir_{i}_1")
                os.mkdir(temp_dir_1)
                connection1 = _make_libp2p_connection(
                    port=DEFAULT_PORT + 1,
                    relay=False,
                    entry_peers=[maddr],
                    data_dir=temp_dir_1,
                )
                multiplexer1 = Multiplexer([connection1])
                self.log_files.append(connection1.node.log_file)
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                temp_dir_2 = os.path.join(self.t, f"dir_{i}_2")
                os.mkdir(temp_dir_2)
                connection2 = _make_libp2p_connection(
                    port=DEFAULT_PORT + 2,
                    relay=False,
                    entry_peers=[maddr],
                    data_dir=temp_dir_2,
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
                envelope = Envelope(to=addr_2, sender=addr_1, message=msg,)

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert (
                    delivered_envelope.protocol_specification_id
                    == envelope.protocol_specification_id
                )
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
                temp_dir_1 = os.path.join(self.t, f"dir_{i}__")
                os.mkdir(temp_dir_1)
                connection1 = _make_libp2p_connection(
                    port=DEFAULT_PORT + 1,
                    relay=False,
                    entry_peers=[PUBLIC_DHT_MADDRS[i]],
                    data_dir=temp_dir_1,
                )
                multiplexer1 = Multiplexer([connection1])
                self.log_files.append(connection1.node.log_file)
                multiplexer1.connect()
                multiplexers.append(multiplexer1)
                addr_1 = connection1.node.address

                for j in range(len(PUBLIC_DHT_MADDRS)):
                    if j == i:
                        continue

                    temp_dir_2 = os.path.join(self.t, f"dir_{i}_{j}")
                    os.mkdir(temp_dir_2)
                    connection2 = _make_libp2p_connection(
                        port=DEFAULT_PORT + 2,
                        relay=False,
                        entry_peers=[PUBLIC_DHT_MADDRS[j]],
                        data_dir=temp_dir_2,
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
                    envelope = Envelope(to=addr_2, sender=addr_1, message=msg,)

                    multiplexer1.put(envelope)
                    delivered_envelope = multiplexer2.get(block=True, timeout=20)

                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert (
                        delivered_envelope.protocol_specification_id
                        == envelope.protocol_specification_id
                    )
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

    def teardown(self):
        """Tear down the test"""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegate:
    """Test that public DHT's delegate service is working properly"""

    def setup(self):
        """Set the test up"""
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        os.chdir(self.t)

    def test_connectivity(self):
        """Test connectivity."""
        for i in range(len(PUBLIC_DHT_DELEGATE_URIS)):
            uri = PUBLIC_DHT_DELEGATE_URIS[i]
            peer_public_key = PUBLIC_DHT_PUBLIC_KEYS[i]
            temp_dir = os.path.join(self.t, f"dir_{i}")
            os.mkdir(temp_dir)
            connection = _make_libp2p_client_connection(
                peer_public_key=peer_public_key, uri=uri, data_dir=temp_dir
            )
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
        """Test communication direct (i.e. both clients registered to same peer)."""
        for i in range(len(PUBLIC_DHT_DELEGATE_URIS)):
            uri = PUBLIC_DHT_DELEGATE_URIS[i]
            peer_public_key = PUBLIC_DHT_PUBLIC_KEYS[i]
            multiplexers = []
            try:
                temp_dir_1 = os.path.join(self.t, f"dir_{i}_1")
                os.mkdir(temp_dir_1)
                connection1 = _make_libp2p_client_connection(
                    peer_public_key=peer_public_key, uri=uri, data_dir=temp_dir_1
                )
                multiplexer1 = Multiplexer([connection1])
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                temp_dir_2 = os.path.join(self.t, f"dir_{i}_2")
                os.mkdir(temp_dir_2)
                connection2 = _make_libp2p_client_connection(
                    peer_public_key=peer_public_key, uri=uri, data_dir=temp_dir_2
                )
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
                envelope = Envelope(to=addr_2, sender=addr_1, message=msg,)

                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=20)

                assert delivered_envelope is not None
                assert delivered_envelope.to == envelope.to
                assert delivered_envelope.sender == envelope.sender
                assert (
                    delivered_envelope.protocol_specification_id
                    == envelope.protocol_specification_id
                )
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
        """Test communication indirect (i.e. clients registered to different peers)."""
        assert (
            len(PUBLIC_DHT_DELEGATE_URIS) > 1
        ), "Test requires at least 2 public dht node"

        for i in range(len(PUBLIC_DHT_DELEGATE_URIS)):
            multiplexers = []
            try:
                temp_dir_1 = os.path.join(self.t, f"dir_{i}__")
                os.mkdir(temp_dir_1)
                connection1 = _make_libp2p_client_connection(
                    peer_public_key=PUBLIC_DHT_PUBLIC_KEYS[i],
                    uri=PUBLIC_DHT_DELEGATE_URIS[i],
                    data_dir=temp_dir_1,
                )
                multiplexer1 = Multiplexer([connection1])
                multiplexer1.connect()
                multiplexers.append(multiplexer1)

                addr_1 = connection1.address

                for j in range(len(PUBLIC_DHT_DELEGATE_URIS)):
                    if j == i:
                        continue

                    temp_dir_2 = os.path.join(self.t, f"dir_{i}_{j}")
                    os.mkdir(temp_dir_2)
                    connection2 = _make_libp2p_client_connection(
                        peer_public_key=PUBLIC_DHT_PUBLIC_KEYS[j],
                        uri=PUBLIC_DHT_DELEGATE_URIS[j],
                        data_dir=temp_dir_2,
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
                    envelope = Envelope(to=addr_2, sender=addr_1, message=msg,)

                    multiplexer1.put(envelope)
                    delivered_envelope = multiplexer2.get(block=True, timeout=20)

                    assert delivered_envelope is not None
                    assert delivered_envelope.to == envelope.to
                    assert delivered_envelope.sender == envelope.sender
                    assert (
                        delivered_envelope.protocol_specification_id
                        == envelope.protocol_specification_id
                    )
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

    def teardown(self):
        """Tear down the test"""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTRelayAEACli(AEATestCaseEmpty):
    """Test that public DHT's relay service is working properly, using aea cli"""

    @libp2p_log_on_failure
    def test_connectivity(self):
        """Test connectivity."""
        self.log_files = []
        self.conn_key_file = os.path.join(
            os.path.abspath(os.getcwd()), "./conn_key.txt"
        )
        self.generate_private_key()
        self.add_private_key()
        self.generate_private_key(private_key_file=self.conn_key_file)
        self.add_private_key(private_key_filepath=self.conn_key_file, connection=True)
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

        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

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


@pytest.mark.integration
class TestLibp2pConnectionPublicDHTDelegateAEACli(AEATestCaseEmpty):
    """Test that public DHT's delegate service is working properly, using aea cli"""

    def test_connectivity(self):
        """Test connectivity."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", str(P2P_CLIENT_CONNECTION_PUBLIC_ID))
        config_path = "vendor.fetchai.connections.p2p_libp2p_client.config"
        self.nested_set_config(
            config_path,
            {"nodes": [{"uri": "{}".format(uri)} for uri in PUBLIC_DHT_DELEGATE_URIS]},
        )
        conn_path = "vendor.fetchai.connections.p2p_libp2p_client"
        self.nested_set_config(
            conn_path + ".config",
            {
                "nodes": [
                    {"uri": uri, "public_key": PUBLIC_DHT_PUBLIC_KEYS[i]}
                    for i, uri in enumerate(PUBLIC_DHT_DELEGATE_URIS)
                ]
            },
        )

        # generate certificates for connection
        self.nested_set_config(
            conn_path + ".cert_requests",
            [
                CertRequest(
                    identifier="acn",
                    ledger_id="fetchai",
                    not_after="2022-01-01",
                    not_before="2021-01-01",
                    public_key=public_key,
                    save_path=f"./cli_test_cert_{public_key}.txt",
                )
                for public_key in PUBLIC_DHT_PUBLIC_KEYS
            ],
        )
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        process = self.run_agent()
        is_running = self.is_running(process, timeout=AEA_DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."

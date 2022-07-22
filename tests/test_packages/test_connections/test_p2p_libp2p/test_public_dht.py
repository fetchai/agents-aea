# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

import itertools
import json
import os

import pytest

from aea.helpers.base import CertRequest
from aea.multiplexer import Multiplexer
from aea.test_tools.test_cases import AEATestCaseMany

from packages.valory.connections import p2p_libp2p, p2p_libp2p_client
from packages.valory.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_CONNECTION_PUBLIC_ID,
)
from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
)
from packages.valory.connections.p2p_libp2p_client.connection import (
    PUBLIC_ID as P2P_CLIENT_CONNECTION_PUBLIC_ID,
)

from tests.conftest import DEFAULT_LEDGER
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    LIBP2P_LEDGER,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
    load_client_connection_yaml_config,
    ports,
)


nodes = load_client_connection_yaml_config()["nodes"]


PUBLIC_DHT_MADDRS = [node["maddr"] for node in nodes]
PUBLIC_DHT_DELEGATE_URIS = [node["uri"] for node in nodes]
PUBLIC_DHT_PUBLIC_KEYS = [node["public_key"] for node in nodes]

AEA_DEFAULT_LAUNCH_TIMEOUT = 30
AEA_LIBP2P_LAUNCH_TIMEOUT = 30

p2p_libp2p_path = f"vendor.{p2p_libp2p.__name__.split('.', 1)[-1]}"
p2p_libp2p_client_path = f"vendor.{p2p_libp2p_client.__name__.split('.', 1)[-1]}"


@pytest.fixture
def maddrs(request):
    """Fixture for multi addresses."""
    return request.param


@pytest.fixture
def delegate_uris_public_keys(request):
    """Fixture for delegate uris and public keys."""
    return request.param


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTRelay(BaseP2PLibp2pTest):
    """Test that public DHT's relay service is working properly"""

    @pytest.mark.parametrize("maddrs", [PUBLIC_DHT_MADDRS], indirect=True)
    def test_connectivity(self, maddrs):
        """Test connectivity."""

        for maddr in maddrs:
            connection = _make_libp2p_connection(relay=False, entry_peers=[maddr])
            multiplexer = Multiplexer([connection])
            self.log_files.append(connection.node.log_file)
            multiplexer.connect()
            assert_msg = f"Couldn't connect to public node {maddr}"
            assert connection.is_connected is True, assert_msg

    @pytest.mark.flaky(reruns=5, reruns_delay=5)
    @pytest.mark.parametrize("maddrs", [PUBLIC_DHT_MADDRS], indirect=True)
    def test_communication_direct(self, maddrs):
        """Test direct communication via each of the multiaddrs."""

        for maddr in maddrs:

            multiplexers = []
            connection1 = _make_libp2p_connection(relay=False, entry_peers=[maddr])
            multiplexer1 = Multiplexer([connection1])
            self.log_files.append(connection1.node.log_file)
            multiplexer1.connect()
            multiplexers.append(multiplexer1)

            connection2 = _make_libp2p_connection(relay=False, entry_peers=[maddr])
            multiplexer2 = Multiplexer([connection2])
            self.log_files.append(connection2.node.log_file)
            multiplexer2.connect()
            multiplexers.append(multiplexer2)

            sender = connection1.address
            to = connection2.address

            envelope = self.enveloped_default_message(to=to, sender=sender)
            multiplexer1.put(envelope)
            delivered_envelope = multiplexer2.get(block=True, timeout=30)
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    @pytest.mark.flaky(reruns=5, reruns_delay=5)
    @pytest.mark.parametrize("maddrs", [PUBLIC_DHT_MADDRS], indirect=True)
    def test_communication_indirect(self, maddrs):
        """Test communication indirect."""

        assert len(maddrs) > 1, "Test requires at least 2 public dht node"

        for i, maddr in enumerate(maddrs):
            multiplexers = []
            connection1 = _make_libp2p_connection(relay=False, entry_peers=[maddr])
            multiplexer1 = Multiplexer([connection1])
            self.log_files.append(connection1.node.log_file)
            multiplexer1.connect()
            multiplexers.append(multiplexer1)
            sender = connection1.address

            for j in range(len(maddrs)):
                if j == i:
                    continue

                connection2 = _make_libp2p_connection(
                    relay=False,
                    entry_peers=[maddrs[j]],
                )
                multiplexer2 = Multiplexer([connection2])
                self.log_files.append(connection2.node.log_file)
                multiplexer2.connect()
                multiplexers.append(multiplexer2)

                to = connection2.address
                envelope = self.enveloped_default_message(to=to, sender=sender)
                multiplexer1.put(envelope)
                delivered_envelope = multiplexer2.get(block=True, timeout=30)

                assert self.sent_is_delivered_envelope(envelope, delivered_envelope)


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTDelegate(BaseP2PLibp2pTest):
    """Test that public DHT's delegate service is working properly"""

    @pytest.mark.parametrize(
        "delegate_uris_public_keys",
        [
            (PUBLIC_DHT_DELEGATE_URIS, PUBLIC_DHT_PUBLIC_KEYS),
        ],
        indirect=True,
    )
    def test_connectivity(self, delegate_uris_public_keys):
        """Test connectivity."""

        for uri, peer_public_key in zip(*delegate_uris_public_keys):

            connection = _make_libp2p_client_connection(
                peer_public_key=peer_public_key, uri=uri
            )
            multiplexer = Multiplexer([connection])

            try:
                multiplexer.connect()
                assert connection.is_connected, f"Couldn't connect to {uri}"
            except Exception:
                raise
            finally:
                multiplexer.disconnect()

    @pytest.mark.parametrize(
        "delegate_uris_public_keys",
        [
            (PUBLIC_DHT_DELEGATE_URIS, PUBLIC_DHT_PUBLIC_KEYS),
        ],
        indirect=True,
    )
    def test_communication_direct(self, delegate_uris_public_keys):
        """Test communication direct (i.e. both clients registered to same peer)."""

        for uri, peer_public_key in zip(*delegate_uris_public_keys):

            multiplexers = []
            connection1 = _make_libp2p_client_connection(
                peer_public_key=peer_public_key, uri=uri
            )
            multiplexer1 = Multiplexer([connection1])
            multiplexer1.connect()
            multiplexers.append(multiplexer1)

            connection2 = _make_libp2p_client_connection(
                peer_public_key=peer_public_key, uri=uri
            )
            multiplexer2 = Multiplexer([connection2])
            multiplexer2.connect()
            multiplexers.append(multiplexer2)

            sender = connection1.address
            to = connection2.address
            envelope = self.enveloped_default_message(to=to, sender=sender)

            multiplexer1.put(envelope)
            delivered_envelope = multiplexer2.get(block=True, timeout=20)
            assert self.sent_is_delivered_envelope(envelope, delivered_envelope)

    @pytest.mark.parametrize(
        "delegate_uris_public_keys",
        [
            (PUBLIC_DHT_DELEGATE_URIS, PUBLIC_DHT_PUBLIC_KEYS),
        ],
        indirect=True,
    )
    def test_communication_indirect(self, delegate_uris_public_keys):
        """Test communication indirect (i.e. clients registered to different peers)."""

        delegate_uris, public_keys = delegate_uris_public_keys
        assert len(delegate_uris) > 1, "Test requires at least 2 public dht node"

        nodes = range(len(delegate_uris))
        for i, j in itertools.permutations(nodes, 2):

            multiplexers = []
            connection1 = _make_libp2p_client_connection(
                peer_public_key=public_keys[i],
                uri=delegate_uris[i],
            )
            multiplexer1 = Multiplexer([connection1])
            multiplexer1.connect()
            multiplexers.append(multiplexer1)

            sender = connection1.address

            connection2 = _make_libp2p_client_connection(
                peer_public_key=public_keys[j],
                uri=delegate_uris[j],
            )
            multiplexer2 = Multiplexer([connection2])
            multiplexer2.connect()
            multiplexers.append(multiplexer2)

            to = connection2.address
            envelope = self.enveloped_default_message(to=to, sender=sender)

            multiplexer1.put(envelope)
            delivered_envelope = multiplexer2.get(block=True, timeout=20)
            self.sent_is_delivered_envelope(envelope, delivered_envelope)


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTRelayAEACli(AEATestCaseMany):
    """Test that public DHT's relay service is working properly, using aea cli"""

    @pytest.mark.parametrize("maddrs", [PUBLIC_DHT_MADDRS], indirect=True)
    def test_connectivity(self, maddrs):
        """Test connectivity."""
        self.log_files = []
        self.agent_name = "some"
        self.create_agents(self.agent_name)
        self.set_agent_context(self.agent_name)
        self.conn_key_file = os.path.join(
            os.path.abspath(os.getcwd()), "./conn_key.txt"
        )
        agent_ledger_id, node_ledger_id = DEFAULT_LEDGER, LIBP2P_LEDGER
        # set config
        self.set_config("agent.default_ledger", agent_ledger_id)
        self.set_config(
            "agent.required_ledgers",
            json.dumps([agent_ledger_id, node_ledger_id]),
            "list",
        )
        self.set_config("agent.default_connection", str(P2P_CONNECTION_PUBLIC_ID))
        # agent keys
        self.generate_private_key(agent_ledger_id)
        self.add_private_key(agent_ledger_id, f"{agent_ledger_id}_private_key.txt")
        # libp2p node keys
        self.generate_private_key(node_ledger_id, private_key_file=self.conn_key_file)
        self.add_private_key(
            node_ledger_id, private_key_filepath=self.conn_key_file, connection=True
        )
        # add connection and build
        self.add_item("connection", str(P2P_CONNECTION_PUBLIC_ID))
        self.run_cli_command("build", cwd=self._get_cwd())
        # for logging
        log_file = f"libp2p_node_{self.agent_name}.log"
        log_file = os.path.join(os.path.abspath(os.getcwd()), log_file)

        config_path = f"{p2p_libp2p_path}.config"
        self.nested_set_config(
            config_path,
            {
                "local_uri": f"127.0.0.1:{next(ports)}",
                "entry_peers": maddrs,
                "log_file": log_file,
                "ledger_id": node_ledger_id,
            },
        )

        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        self.log_files = [log_file]
        process = self.run_agent()

        is_running = self.is_running(process, timeout=AEA_LIBP2P_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "Peer running in "
        missing_strings = self.missing_from_output(process, check_strings)
        assert not missing_strings

        self.terminate_agents(process)
        assert self.is_successfully_terminated(process)

    def teardown(self):
        """Clean up after test case run."""
        self.unset_agent_context()
        self.run_cli_command("delete", self.agent_name)


@pytest.mark.integration
@libp2p_log_on_failure_all
class TestLibp2pConnectionPublicDHTDelegateAEACli(AEATestCaseMany):
    """Test that public DHT's delegate service is working properly, using aea cli"""

    @pytest.mark.parametrize(
        "delegate_uris_public_keys",
        [
            (PUBLIC_DHT_DELEGATE_URIS, PUBLIC_DHT_PUBLIC_KEYS),
        ],
        indirect=True,
    )
    def test_connectivity(self, delegate_uris_public_keys):
        """Test connectivity."""

        delegate_uris, public_keys = delegate_uris_public_keys
        self.agent_name = "some"
        self.create_agents(self.agent_name)
        self.set_agent_context(self.agent_name)

        agent_ledger_id, node_ledger_id = DEFAULT_LEDGER, LIBP2P_LEDGER
        self.set_config("agent.default_ledger", agent_ledger_id)
        self.set_config(
            "agent.required_ledgers",
            json.dumps([agent_ledger_id, node_ledger_id]),
            "list",
        )
        # agent keys
        self.generate_private_key(agent_ledger_id)
        self.add_private_key(agent_ledger_id, f"{agent_ledger_id}_private_key.txt")

        self.add_item("connection", str(P2P_CLIENT_CONNECTION_PUBLIC_ID))
        config_path = f"{p2p_libp2p_client_path}.config"
        self.nested_set_config(
            config_path,
            {"nodes": [{"uri": uri} for uri in delegate_uris]},
        )
        self.nested_set_config(
            p2p_libp2p_client_path + ".config",
            {
                "nodes": [
                    {"uri": uri, "public_key": public_keys[i]}
                    for i, uri in enumerate(delegate_uris)
                ]
            },
        )

        # generate certificates for connection
        self.nested_set_config(
            p2p_libp2p_client_path + ".cert_requests",
            [
                CertRequest(
                    identifier="acn",
                    ledger_id=agent_ledger_id,
                    not_before=LIBP2P_CERT_NOT_BEFORE,
                    not_after=LIBP2P_CERT_NOT_AFTER,
                    public_key=public_key,
                    message_format="{public_key}",
                    save_path=f"./cli_test_cert_{public_key}.txt",
                )
                for public_key in public_keys
            ],
        )
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        process = self.run_agent()
        is_running = self.is_running(process, timeout=AEA_DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"
        self.terminate_agents(process)
        assert self.is_successfully_terminated(process)

    def teardown(self):
        """Clean up after test case run."""
        self.unset_agent_context()
        self.run_cli_command("delete", self.agent_name)

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

"""This test module contains AEA cli tests for Libp2p tcp client connection."""

import json

from aea.multiplexer import Multiplexer
from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.valory.connections import p2p_libp2p_client
from packages.valory.connections.p2p_libp2p_client.connection import PUBLIC_ID

from tests.conftest import DEFAULT_LEDGER, LOCALHOST
from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    _make_libp2p_connection,
    libp2p_log_on_failure_all,
    make_cert_request,
    ports,
)


DEFAULT_HOST = LOCALHOST.hostname
DEFAULT_CLIENTS_PER_NODE = 4
DEFAULT_LAUNCH_TIMEOUT = 10


@libp2p_log_on_failure_all
class TestP2PLibp2pClientConnectionAEARunning(AEATestCaseEmpty):
    """Test AEA with client connection is correctly run"""

    conn_path = f"vendor.{p2p_libp2p_client.__name__.split('.', 1)[-1]}"
    public_id = str(PUBLIC_ID)
    port = next(ports)
    uri = f"{DEFAULT_HOST}:{port}"
    kwargs = dict(
        delegate_host=DEFAULT_HOST,
        delegate_port=port,
        delegate=True,
    )

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        super().setup_class()
        cls.node_connection = _make_libp2p_connection(**cls.kwargs)
        cls.node_multiplexer = Multiplexer([cls.node_connection])
        cls.log_files = [cls.node_connection.node.log_file]
        cls.node_multiplexer.connect()
        node = {"uri": cls.uri, "public_key": cls.node_connection.node.pub}
        cls.nodes = {"nodes": [node]}
        cls.expected = (f"Successfully connected to libp2p node {cls.uri}",)

    def test_node(self):
        """Test the node is connected."""
        assert self.node_connection.is_connected is True

    def test_connection(self):
        """Test the connection can be used in an aea."""
        ledger_id = DEFAULT_LEDGER
        self.generate_private_key(ledger_id)
        self.add_private_key(ledger_id, f"{ledger_id}_private_key.txt")
        self.set_config("agent.default_ledger", ledger_id)
        self.set_config("agent.required_ledgers", json.dumps([ledger_id]), "list")
        self.add_item("connection", self.public_id)
        self.nested_set_config(self.conn_path + ".config", self.nodes)

        # generate certificates for connection
        self.nested_set_config(
            self.conn_path + ".cert_requests",
            [make_cert_request(self.node_connection.node.pub, ledger_id, "./cli_test")],
        )
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        process = self.run_agent()
        is_running = self.is_running(process, timeout=DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"
        missing_strings = self.missing_from_output(process, self.expected)
        assert not missing_strings
        self.terminate_agents(process)
        assert self.is_successfully_terminated(process)

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""
        cls.terminate_agents()
        cls.node_multiplexer.disconnect()
        super().teardown_class()

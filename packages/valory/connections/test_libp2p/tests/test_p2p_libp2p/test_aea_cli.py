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

"""This test module contains AEA cli tests for P2PLibp2p connection."""

# pylint: skip-file

import json

from aea.configurations.constants import DEFAULT_LEDGER
from aea.test_tools.network import LOCALHOST

from packages.valory.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_CONNECTION_PUBLIC_ID,
)
from packages.valory.connections.p2p_libp2p.tests.base import (
    libp2p_log_on_failure_all,
    ports,
)
from packages.valory.connections.p2p_libp2p.tests.test_aea_cli import (
    BaseP2PLibp2pConnectionAEATest,
    p2p_libp2p_path,
)
from packages.valory.connections.test_libp2p.tests.base import LIBP2P_LEDGER


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionAEARunningDefaultConfigNode(
    BaseP2PLibp2pConnectionAEATest
):
    """Test AEA with p2p_libp2p connection is correctly run"""

    def test_agent(self) -> None:
        """Test with aea."""
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
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        self.set_logging()
        self.run_aea_cli_test()


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionAEARunningFullNode(BaseP2PLibp2pConnectionAEATest):
    """Test AEA with p2p_libp2p connection is correctly run"""

    def test_agent(self) -> None:
        """Test with aea."""
        agent_ledger_id, node_ledger_id = DEFAULT_LEDGER, LIBP2P_LEDGER
        # set config
        self.set_config("agent.default_ledger", agent_ledger_id)
        self.set_config(
            "agent.required_ledgers",
            json.dumps([agent_ledger_id, node_ledger_id]),
            "list",
        )
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

        # setup a full node: with public uri, relay service, and delegate service
        config_path = f"{p2p_libp2p_path}.config"
        hostname = LOCALHOST.hostname
        self.set_config(f"{config_path}.local_uri", f"{hostname}:{next(ports)}")
        self.set_config(f"{config_path}.public_uri", f"{hostname}:{next(ports)}")
        self.set_config(f"{config_path}.delegate_uri", f"{hostname}:{next(ports)}")

        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        self.set_logging()
        self.run_aea_cli_test()

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

import json
import os
from pathlib import Path
from typing import List

from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum.ethereum import EthereumCrypto as Ethereum

from aea.test_tools.test_cases import AEATestCaseEmpty

from packages.valory.connections import p2p_libp2p
from packages.valory.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_CONNECTION_PUBLIC_ID,
)
from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
)
from packages.valory.connections.p2p_libp2p.tests.base import libp2p_log_on_failure_all


p2p_libp2p_path = f"vendor.{p2p_libp2p.__name__.split('.', 1)[-1]}"
DEFAULT_NET_SIZE = 4
LIBP2P_LAUNCH_TIMEOUT = 20  # may downloads up to ~66Mb


class BaseP2PLibp2pConnectionAEATest(AEATestCaseEmpty):
    """Base class for AEA CLI tests"""

    log_files: List[str] = []
    capture_log = True

    package_registry_src_rel = Path(__file__).parent.parent.parent.parent.parent
    conn_key_file: str

    @classmethod
    def setup_class(cls) -> None:
        """Set the test up"""
        super().setup_class()
        cls.conn_key_file = os.path.join(os.path.abspath(os.getcwd()), "./conn_key.txt")
        cls.log_files = []

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down the test"""
        cls.log_files.clear()
        super().teardown_class()

    def set_logging(self) -> None:
        """Set logging"""

        config_path = f"{p2p_libp2p_path}.config"
        log_file = f"libp2p_node_{self.agent_name}.log"
        log_file = os.path.join(os.path.abspath(os.getcwd()), log_file)
        self.set_config(f"{config_path}.log_file", log_file)
        self.log_files.append(log_file)

    def run_aea_cli_test(self) -> None:
        """Run the agent, check strings and terminate"""

        process = self.run_agent()
        is_running = self.is_running(process, timeout=LIBP2P_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "Peer running in "
        missing_strings = self.missing_from_output(process, check_strings)
        assert not missing_strings


@libp2p_log_on_failure_all
class TestP2PLibp2pConnectionAEARunningEthereumConfigNode(
    BaseP2PLibp2pConnectionAEATest
):
    """Test AEA with p2p_libp2p connection is correctly run"""

    conn_key_file: str

    def test_agent(self) -> None:
        """Test with aea."""
        key_path = "ethereum_private_key.txt"
        self.generate_private_key(
            ledger_api_id=Ethereum.identifier, private_key_file=key_path
        )
        self.add_private_key(
            ledger_api_id=Ethereum.identifier, private_key_filepath=key_path
        )
        self.generate_private_key(
            CosmosCrypto.identifier, private_key_file=self.conn_key_file
        )
        self.add_private_key(
            CosmosCrypto.identifier,
            private_key_filepath=self.conn_key_file,
            connection=True,
        )
        self.add_item("connection", str(P2P_CONNECTION_PUBLIC_ID))
        self.run_cli_command("build", cwd=self._get_cwd())
        self.set_config("agent.default_ledger", Ethereum.identifier)
        self.nested_set_config(
            "agent.required_ledgers", [CosmosCrypto.identifier, Ethereum.identifier]
        )
        self.set_config("agent.default_connection", str(P2P_CONNECTION_PUBLIC_ID))

        setting_path = f"{p2p_libp2p_path}.cert_requests"
        settings = json.dumps(
            [
                {
                    "identifier": "acn",
                    "ledger_id": Ethereum.identifier,
                    "not_before": LIBP2P_CERT_NOT_BEFORE,
                    "not_after": LIBP2P_CERT_NOT_AFTER,
                    "public_key": CosmosCrypto.identifier,
                    "message_format": "{public_key}",
                    "save_path": ".certs/conn_cert.txt",
                }
            ]
        )
        self.set_config(setting_path, settings, type_="list")
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())

        self.set_logging()
        self.run_aea_cli_test()

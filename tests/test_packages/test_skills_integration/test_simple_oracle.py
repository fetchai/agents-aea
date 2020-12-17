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
"""This test module contains the integration test for the generic buyer and seller skills."""

import pytest

from aea.test_tools.test_cases import AEATestCaseMany

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_FILE,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
    MAX_FLAKY_RERUNS_ETH,
    UseGanache,
)


@pytest.mark.integration
class TestOracleSkills(AEATestCaseMany, UseGanache):
    """Test that oracle skills work."""

    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_oracle(self, erc20_contract, oracle_contract):
        """Run the oracle skills sequence."""
        oracle_agent_name = "oracle_aea"
        client_agent_name = "client_aea"

        self.create_agents(oracle_agent_name, client_agent_name)

        # add ethereum ledger in both configuration files
        default_routing = {
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/contract_api:0.9.0": "fetchai/ledger:0.11.0",
            "fetchai/http:0.10.0": "fetchai/http_client:0.15.0",
            "fetchai/prometheus:0.1.0": "fetchai/prometheus:0.1.0",
        }

        # add packages for oracle agent
        self.set_agent_context(oracle_agent_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.13.0")
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.add_item("connection", "fetchai/http_client:0.15.0")
        self.add_item("connection", "fetchai/prometheus:0.1.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.13.0")
        self.set_config("agent.default_ledger", ETHEREUM)
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.add_item("skill", "fetchai/coin_price:0.2.0")
        self.add_item("contract", "fetchai/oracle:0.2.0")
        self.add_item("skill", "fetchai/simple_oracle:0.2.0")

        # set erc20 address
        _, erc20_address = erc20_contract
        _, oracle_address = oracle_contract

        setting_path = (
            "vendor.fetchai.skills.simple_oracle.models.strategy.args.erc20_address"
        )
        self.set_config(setting_path, erc20_address)
        setting_path = (
            "vendor.fetchai.skills.simple_oracle.models.strategy.args.contract_address"
        )
        self.set_config(setting_path, oracle_address)

        self.generate_private_key(ETHEREUM)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_3, ETHEREUM_PRIVATE_KEY_FILE
        )

        self.run_install()

        # add packages for agent two
        self.set_agent_context(client_agent_name)
        self.add_item("connection", "fetchai/ledger:0.11.0")
        self.remove_item("connection", "fetchai/stub:0.13.0")
        self.set_config("agent.default_connection", "fetchai/ledger:0.11.0")
        self.set_config("agent.default_ledger", ETHEREUM)

        default_routing = {
            "fetchai/ledger_api:0.8.0": "fetchai/ledger:0.11.0",
            "fetchai/contract_api:0.9.0": "fetchai/ledger:0.11.0",
        }
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)
        self.add_item("contract", "fetchai/oracle_client:0.1.0")
        self.add_item("contract", "fetchai/fet_erc20:0.1.0")
        self.add_item("skill", "fetchai/simple_oracle_client:0.1.0")

        setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.erc20_address"
        self.set_config(setting_path, erc20_address)
        setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address"
        self.set_config(setting_path, oracle_address)

        self.generate_private_key(ETHEREUM)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_2, ETHEREUM_PRIVATE_KEY_FILE
        )

        # run oracle agent
        self.set_agent_context(oracle_agent_name)
        self.run_cli_command("build", cwd=self._get_cwd())
        oracle_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            oracle_aea_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        check_strings = (
            "setting up HttpHandler",
            "setting up CoinPriceBehaviour",
            "Setting up Fetch oracle contract...",
            "Fetching price of fetch-ai in usd from https://api.coingecko.com/api/v3/",
            "received raw transaction=",
            "fetch-ai price =",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "Oracle role successfully granted!",
            "Oracle value successfully updated!",
        )
        missing_strings = self.missing_from_output(
            oracle_aea_process, check_strings, timeout=60, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        # run oracle client agent
        self.set_agent_context(client_agent_name)
        client_aea_process = self.run_agent()

        check_strings = (
            "requesting contract deployment transaction...",
            "received raw transaction=",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "Oracle client contract successfully deployed!",
            "Oracle client transactions approved!",
            "Oracle value successfully requested!",
        )
        missing_strings = self.missing_from_output(
            client_aea_process, check_strings, timeout=60, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        self.terminate_agents(oracle_aea_process, client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."

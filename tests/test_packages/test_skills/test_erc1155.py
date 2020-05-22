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

from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from ...conftest import FUNDED_ETH_PRIVATE_KEY_1, FUNDED_ETH_PRIVATE_KEY_2


@pytest.mark.unstable
class TestERCSkillsEthereumLedger(AEATestCaseMany, UseOef):
    """Test that erc1155 skills work."""

    def test_generic(self):
        """Run the generic skills sequence."""
        deploy_aea_name = "deploy_aea"
        client_aea_name = "client_aea"

        self.create_agents(deploy_aea_name, client_aea_name)

        # add ethereum ledger in both configuration files
        ledger_apis = {
            "ethereum": {
                "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
                "chain_id": 3,
                "gas_price": 50,
            }
        }
        setting_path = "agent.ledger_apis"

        # add packages for agent one
        self.set_agent_context(deploy_aea_name)
        self.force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.3.0")
        self.set_config("agent.default_ledger", "ethereum")
        self.add_item("skill", "fetchai/erc1155_deploy:0.4.0")

        diff = self.difference_to_fetched_agent(
            "fetchai/erc1155_deployer:0.4.0", deploy_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "eth_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, "eth_private_key.txt"
        )
        # stdout = self.get_wealth("ethereum")
        # if int(stdout) < 100000000000000000:
        #     pytest.skip("The agent needs more funds for the test to pass.")
        self.run_install()

        # add packages for agent two
        self.set_agent_context(client_aea_name)
        self.force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.3.0")
        self.set_config("agent.default_ledger", "ethereum")
        self.add_item("skill", "fetchai/erc1155_client:0.3.0")

        diff = self.difference_to_fetched_agent(
            "fetchai/erc1155_client:0.4.0", client_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "eth_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_2, "eth_private_key.txt"
        )
        # stdout = self.get_wealth("ethereum")
        # if int(stdout) < 100000000000000000:
        #     pytest.skip("The agent needs more funds for the test to pass.")
        self.run_install()

        # run agents
        self.set_agent_context(deploy_aea_name)
        deploy_aea_process = self.run_agent("--connections", "fetchai/oef:0.3.0")

        check_strings = (
            "updating erc1155 service on OEF search node.",
            "unregistering erc1155 service from OEF search node.",
            "Successfully deployed the contract. Transaction digest:",
            "Successfully created items. Transaction digest:",
            "Successfully minted items. Transaction digest:",
        )
        missing_strings = self.missing_from_output(
            deploy_aea_process, check_strings, timeout=420, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        self.set_agent_context(client_aea_name)
        client_aea_process = self.run_agent("--connections", "fetchai/oef:0.3.0")

        check_strings = (
            "Sending PROPOSE to agent=",
            "received ACCEPT_W_INFORM from sender=",
            "Successfully conducted atomic swap. Transaction digest:",
        )
        missing_strings = self.missing_from_output(
            deploy_aea_process, check_strings, timeout=360, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received valid PROPOSE from sender=",
            "sending ACCEPT_W_INFORM to agent=",
        )
        missing_strings = self.missing_from_output(
            client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in client_aea output.".format(missing_strings)

        self.terminate_agents(deploy_aea_process, client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."

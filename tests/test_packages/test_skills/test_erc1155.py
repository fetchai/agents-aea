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

import time

from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEATestCaseMany, UseOef


class TestERCSkillsEthereumLedger(AEATestCaseMany, UseOef):
    """Test that erc1155 skills work."""

    @skip_test_ci
    def test_generic(self, pytestconfig):
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
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/erc1155_deploy:0.2.0")
        self.run_install()

        # add packages for agent two
        self.set_agent_context(client_aea_name)
        self.force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/erc1155_client:0.2.0")
        self.run_install()

        # run agents
        self.set_agent_context(deploy_aea_name)
        deploy_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(client_aea_name)
        client_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        # TODO: finish adding string checks
        time.sleep(10.0)

        self.terminate_agents(deploy_aea_process, client_aea_process)

        assert self.is_successfully_terminated(), "ERC1155 test not successful."

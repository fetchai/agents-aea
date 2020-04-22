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

import os
import signal
import time

from aea.crypto.ethereum import ETHEREUM as ETHEREUM_NAME
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.generic import force_set_config
from aea.test_tools.test_cases import AEAWithOefTestCase


class TestGenericSkills(AEAWithOefTestCase):
    """Test that erc1155 skills work."""

    @skip_test_ci
    def test_generic(self, pytestconfig):
        """Run the generic skills sequence."""
        self.initialize_aea()

        deploy_aea_name = "deploy_aea"
        client_aea_name = "client_aea"

        self.create_agents(deploy_aea_name, client_aea_name)

        # add ethereum ledger in both configuration files
        ledger_apis = {
            ETHEREUM_NAME: {
                "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
                "chain_id": 3,
                "gas_price": 50,
            }
        }
        setting_path = "agent.ledger_apis"

        # add packages for agent one
        deploy_aea_dir_path = os.path.join(self.t, deploy_aea_name)
        os.chdir(deploy_aea_dir_path)
        force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/erc1155_deploy:0.2.0")
        self.run_install()

        # add packages for agent two
        client_aea_dir_path = os.path.join(self.t, client_aea_name)
        os.chdir(client_aea_dir_path)
        force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/erc1155_client:0.1.0")
        self.run_install()

        # run agents
        os.chdir(deploy_aea_dir_path)
        deploy_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(client_aea_dir_path)
        client_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        time.sleep(10.0)

        deploy_aea_process.send_signal(signal.SIGINT)
        deploy_aea_process.wait(timeout=10)
        client_aea_process.send_signal(signal.SIGINT)
        client_aea_process.wait(timeout=10)

        # TODO: check the erc1155 run ends
        # TODO uncomment these to test success!
        # assert deploy_aea_process.returncode == 0
        # assert client_aea_process.returncode == 0

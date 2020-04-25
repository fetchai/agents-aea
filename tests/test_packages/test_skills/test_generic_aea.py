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
import time

from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.generic import force_set_config
from aea.test_tools.test_cases import AEAWithOefTestCase


class TestGenericSkills(AEAWithOefTestCase):
    """Test that generic skills work."""

    @skip_test_ci
    def test_generic(self, pytestconfig):
        """Run the generic skills sequence."""
        self.initialize_aea()

        seller_aea_name = "my_generic_seller"
        buyer_aea_name = "my_generic_buyer"
        self.create_agents(seller_aea_name, buyer_aea_name)

        setting_path = "agent.ledger_apis"
        ledger_apis = {FETCHAI_NAME: {"network": "testnet"}}

        # prepare seller agent
        seller_aea_dir_path = os.path.join(self.t, seller_aea_name)
        os.chdir(seller_aea_dir_path)

        force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/generic_seller:0.2.0")
        self.run_install()

        # prepare buyer agent
        buyer_aea_dir_path = os.path.join(self.t, buyer_aea_name)
        os.chdir(buyer_aea_dir_path)

        force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/generic_buyer:0.2.0")
        self.run_install()

        # run AEAs
        os.chdir(seller_aea_dir_path)
        seller_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(buyer_aea_dir_path)
        buyer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        time.sleep(10.0)

        self.terminate_agents([seller_aea_process, buyer_aea_process])

        assert self.is_successfully_terminated(), "Carpark test not successful."

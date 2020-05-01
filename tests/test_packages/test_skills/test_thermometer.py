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

"""This test module contains the integration test for the thermometer skills."""

import time

from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.test_tools.test_cases import AEATestCaseMany, UseOef


class TestThermometerSkill(AEATestCaseMany, UseOef):
    """Test that thermometer skills work."""

    def test_thermometer(self, pytestconfig):
        """Run the thermometer skills sequence."""

        thermometer_aea_name = "my_thermometer"
        thermometer_client_aea_name = "my_thermometer_client"
        self.create_agents(thermometer_aea_name, thermometer_client_aea_name)

        ledger_apis = {FETCHAI_NAME: {"network": "testnet"}}

        # add packages for agent one and run it
        self.set_agent_context(thermometer_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/thermometer:0.1.0")

        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)
        setting_path = (
            "vendor.fetchai.skills.thermometer.models.strategy.args.has_sensor"
        )
        self.set_config(setting_path, False, "bool")

        self.run_install()

        # add packages for agent two and run it
        self.set_agent_context(thermometer_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/thermometer_client:0.1.0")
        self.run_install()

        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)

        self.generate_private_key()
        self.add_private_key()
        self.generate_wealth()

        # run AEAs
        self.set_agent_context(thermometer_aea_name)
        thermometer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(thermometer_client_aea_name)
        thermometer_client_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.2.0"
        )

        self.start_tty_read_thread(thermometer_aea_process)
        self.start_error_read_thread(thermometer_aea_process)
        self.start_tty_read_thread(thermometer_client_aea_process)
        self.start_error_read_thread(thermometer_client_aea_process)

        time.sleep(20)

        self.terminate_agents()

        assert self.is_successfully_terminated(), "Thermometer test not successful."

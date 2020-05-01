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

"""This test module contains the integration test for the weather skills."""

import time

from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEATestCaseMany, UseOef


class TestWeatherSkillsFetchaiLedger(AEATestCaseMany, UseOef):
    """Test that weather skills work."""

    @skip_test_ci
    def test_weather(self, pytestconfig):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        # prepare ledger configurations
        ledger_apis = {FETCHAI_NAME: {"network": "testnet"}}

        # add packages for agent one and run it
        self.set_agent_context(weather_station_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.1.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.run_install()

        # add packages for agent two and run it
        self.set_agent_context(weather_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.1.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.run_install()

        self.generate_private_key()
        self.add_private_key()
        self.generate_wealth()

        self.set_agent_context(weather_station_aea_name)
        process_one = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(weather_client_aea_name)
        process_two = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_tty_read_thread(process_one)
        self.start_error_read_thread(process_one)
        self.start_tty_read_thread(process_two)
        self.start_error_read_thread(process_two)

        time.sleep(10)

        self.terminate_agents()

        assert self.is_successfully_terminated(), "Weather ledger test not successful."

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

import os
import signal
import time

import pytest

from aea.test_tools.test_cases import AEAWithOefTestCase


class TestWeatherSkills(AEAWithOefTestCase):
    """Test that weather skills work."""

    def test_weather(self, pytestconfig):
        """Run the weather skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        agent_name_one = "my_weather_station"
        agent_name_two = "my_weather_client"

        self.initialize_aea()
        self.create_agents(agent_name_one, agent_name_two)

        # prepare agent one (weather station)
        agent_one_dir_path = os.path.join(self.t, agent_name_one)
        os.chdir(agent_one_dir_path)

        self.add_item("connection", "fetchai/oef:0.1.0")
        self.add_item("skill", "fetchai/weather_station:0.1.0")
        self.disable_ledger_tx("fetchai", "skill", "weather_station")
        self.run_install()

        # prepare agent two (weather client)
        agent_two_dir_path = os.path.join(self.t, agent_name_two)
        os.chdir(agent_two_dir_path)

        self.add_item("connection", "fetchai/oef:0.1.0")
        self.add_item("skill", "fetchai/weather_client:0.1.0")
        self.disable_ledger_tx("fetchai", "skill", "weather_client")
        self.run_install()

        # run agents
        os.chdir(agent_one_dir_path)
        process_one = self.run_agent_with_oef()

        os.chdir(agent_two_dir_path)
        process_two = self.run_agent_with_oef()

        # TODO increase timeout so we are sure they work until the end of negotiation.
        time.sleep(5.0)
        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=10)
        process_two.send_signal(signal.SIGINT)
        process_two.wait(timeout=10)

        assert process_one.returncode == 0
        assert process_two.returncode == 0

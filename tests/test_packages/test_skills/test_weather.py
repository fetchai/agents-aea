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

from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEAWithOefTestCase


class TestWeatherSkills(AEAWithOefTestCase):
    """Test that weather skills work."""

    @skip_test_ci
    def test_weather(self, pytestconfig):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"

        self.initialize_aea()
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        # prepare agent one (weather station)
        weather_station_aea_dir_path = os.path.join(self.t, weather_station_aea_name)
        os.chdir(weather_station_aea_dir_path)

        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.1.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        self.run_install()

        # prepare agent two (weather client)
        weather_client_aea_dir_path = os.path.join(self.t, weather_client_aea_name)
        os.chdir(weather_client_aea_dir_path)

        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.1.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_client.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        self.run_install()

        # run agents
        os.chdir(weather_station_aea_dir_path)
        process_one = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(weather_client_aea_dir_path)
        process_two = self.run_agent("--connections", "fetchai/oef:0.2.0")

        time.sleep(10.0)
        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=10)
        process_two.send_signal(signal.SIGINT)
        process_two.wait(timeout=10)

        assert process_one.returncode == 0
        assert process_two.returncode == 0

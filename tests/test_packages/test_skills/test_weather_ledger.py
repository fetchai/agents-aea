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
from pathlib import Path

from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEAWithOefTestCase


class TestWeatherSkillsFetchaiLedger(AEAWithOefTestCase):
    """Test that weather skills work."""

    @skip_test_ci
    def test_weather(self, pytestconfig):
        """Run the weather skills sequence."""

        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"

        self.add_scripts_folder()

        self.initialize_aea()
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        # add fetchai ledger in both configuration files
        find_text = "ledger_apis: {}"
        replace_text = """ledger_apis:
        fetchai:
            network: testnet"""

        weather_station_aea_config = Path(
            weather_station_aea_name, DEFAULT_AEA_CONFIG_FILE
        )
        weather_station_aea_config_content = weather_station_aea_config.read_text()
        weather_station_aea_config_content = weather_station_aea_config_content.replace(
            find_text, replace_text
        )
        weather_station_aea_config.write_text(weather_station_aea_config_content)

        weather_client_aea_config = Path(
            weather_client_aea_name, DEFAULT_AEA_CONFIG_FILE
        )
        weather_client_aea_config_content = weather_client_aea_config.read_text()
        weather_client_aea_config_content = weather_client_aea_config_content.replace(
            find_text, replace_text
        )
        weather_client_aea_config.write_text(weather_client_aea_config_content)

        # add packages for agent one and run it
        weather_station_aea_dir_path = os.path.join(self.t, weather_station_aea_name)
        os.chdir(weather_station_aea_dir_path)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.1.0")
        self.run_install()

        # add packages for agent two and run it
        weather_client_aea_dir_path = os.path.join(self.t, weather_client_aea_name)
        os.chdir(weather_client_aea_dir_path)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.1.0")
        self.run_install()

        self.generate_private_key()
        self.add_private_key()
        self.generate_wealth()

        os.chdir(weather_station_aea_dir_path)
        process_one = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(weather_client_aea_dir_path)
        process_two = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_tty_read_thread(process_one)
        self.start_error_read_thread(process_one)
        self.start_tty_read_thread(process_two)
        self.start_error_read_thread(process_two)

        time.sleep(10)
        process_one.send_signal(signal.SIGINT)
        process_two.send_signal(signal.SIGINT)

        process_one.wait(timeout=10)
        process_two.wait(timeout=10)

        # text1, err1 = process_one.communicate()
        # text2, err2 = process_two.communicate()

        assert process_one.returncode == 0
        assert process_two.returncode == 0

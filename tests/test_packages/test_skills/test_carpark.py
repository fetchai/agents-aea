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


class TestCarPark(AEAWithOefTestCase):
    """Test that carpark skills work."""

    def test_carpark(self, pytestconfig):
        """Run the weather skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        self.initialize_aea()

        agent_name_one = "my_carpark_aea"
        agent_name_two = "my_carpark_client_aea"
        self.create_agents(agent_name_one, agent_name_two)

        # Setup agent one
        agent_one_dir_path = os.path.join(self.t, agent_name_one)
        os.chdir(agent_one_dir_path)
        self.add_item("connection", "fetchai/oef:0.1.0")
        self.add_item("skill", "fetchai/carpark_detection:0.1.0")
        self.run_install()

        # Load the skill yaml file and manually insert the things we need
        setting_path = "vendor.fetchai.skills.carpark_detection.models.strategy.args.db_is_rel_to_cwd"
        self.set_config(setting_path, False)

        # Load the agent yaml file and manually insert the things we need (ledger APIs)

        # TODO: remove this block and replace with next two commented lines
        # when "aea config set" will be able to handle dictionaties and non-existing keys

        # setting_path = "agent.ledger_apis.fetchai.network"
        # self.set_config(setting_path, "testnet")

        # agent config update block start
        file = open("aea-config.yaml", mode="r")

        # read all lines at once
        whole_file = file.read()

        # add in the ledger address
        find_text = "ledger_apis: {}"
        replace_text = """ledger_apis:
        fetchai:
            network: testnet"""

        whole_file = whole_file.replace(find_text, replace_text)

        # close the file
        file.close()

        with open("aea-config.yaml", "w") as f:
            f.write(whole_file)
        # agent config update block end

        # Setup Agent two
        agent_two_dir_path = os.path.join(self.t, agent_name_two)
        os.chdir(agent_two_dir_path)

        self.add_item("connection", "fetchai/oef:0.1.0")
        self.add_item("skill", "fetchai/carpark_client:0.1.0")
        self.run_install()

        # TODO: same as above. Remove this block and replace with next two commented lines
        # when "aea config set" will be able to handle dictionaties and non-existing keys

        # setting_path = "agent.ledger_apis.fetchai.network"
        # self.set_config(setting_path, "testnet")

        # agent config update block start
        file = open("aea-config.yaml", mode="r")

        # read all lines at once
        whole_file = file.read()

        # add in the ledger address
        find_text = "ledger_apis: {}"
        replace_text = """ledger_apis:
        fetchai:
            network: testnet"""

        whole_file = whole_file.replace(find_text, replace_text)

        # close the file
        file.close()

        with open("aea-config.yaml", "w") as f:
            f.write(whole_file)
        # agent config update block end

        # Generate and add private keys
        self.generate_private_key()
        self.add_private_key()

        # Add some funds to the car park client
        self.generate_wealth()

        # Fire the sub-processes and the threads.
        os.chdir(agent_one_dir_path)
        process_one = self.run_agent_with_oef()

        os.chdir(agent_two_dir_path)
        process_two = self.run_agent_with_oef()

        self.start_tty_read_thread(process_one)
        self.start_error_read_thread(process_one)
        self.start_tty_read_thread(process_two)
        self.start_error_read_thread(process_two)

        time.sleep(10)
        process_one.send_signal(signal.SIGINT)
        process_two.send_signal(signal.SIGINT)

        process_one.wait(timeout=10)
        process_two.wait(timeout=10)

        assert process_one.returncode == 0
        assert process_two.returncode == 0

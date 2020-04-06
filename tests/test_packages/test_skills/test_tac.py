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

"""This test module contains the integration test for the tac skills."""

import os
import signal
import time

import pytest

from aea.test_tools.test_cases import AeaWithOefTestCase


class TestTacSkills(AeaWithOefTestCase):
    """Test that tac skills work."""

    def test_tac(self, pytestconfig):
        """Run the tac skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        agent_name_one = "tac_participant_one"
        agent_name_two = "tac_participant_two"
        tac_controller_name = "tac_controller"

        # create tac controller, agent one and agent two
        self.create_agents(
            agent_name_one, agent_name_two, tac_controller_name,
        )

        # prepare tac controller for test
        tac_controller_dir_path = os.path.join(self.t, tac_controller_name)
        os.chdir(tac_controller_dir_path)
        self.add_item("connection", "fetchai/oef:0.1.0")
        self.add_item("contract", "fetchai/erc1155:0.1.0")
        self.add_item("skill", "fetchai/tac_control:0.1.0")
        self.run_install()

        # prepare agents for test
        agent_one_dir_path = os.path.join(self.t, agent_name_one)
        agent_two_dir_path = os.path.join(self.t, agent_name_two)

        for agent_path in (agent_one_dir_path, agent_two_dir_path):
            os.chdir(agent_path)

            self.add_item("connection", "fetchai/oef:0.1.0")
            self.add_item("contract", "fetchai/erc1155:0.1.0")
            self.add_item("skill", "fetchai/tac_participation:0.1.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.1.0")

            self.run_install()

        try:
            # run tac controller
            os.chdir(tac_controller_dir_path)
            tac_controller_process = self.run_oef_subprocess()

            # run two agents (participants)
            os.chdir(agent_one_dir_path)
            agent_one_process = self.run_oef_subprocess()

            os.chdir(agent_two_dir_path)
            agent_two_process = self.run_oef_subprocess()

            time.sleep(10.0)
            agent_one_process.send_signal(signal.SIGINT)
            agent_one_process.wait(timeout=10)

            agent_two_process.send_signal(signal.SIGINT)
            agent_two_process.wait(timeout=10)

            tac_controller_process.send_signal(signal.SIGINT)
            tac_controller_process.wait(timeout=10)

            assert agent_one_process.returncode == 0
            assert agent_two_process.returncode == 0
            assert tac_controller_process.returncode == 0
        finally:
            poll_one = agent_one_process.poll()
            if poll_one is None:
                agent_one_process.terminate()
                agent_one_process.wait(2)

            poll_two = agent_two_process.poll()
            if poll_two is None:
                agent_two_process.terminate()
                agent_two_process.wait(2)

            poll_tac = tac_controller_process.poll()
            if poll_tac is None:
                tac_controller_process.terminate()
                tac_controller_process.wait(2)

        os.chdir(self.t)
        self.delete_agents(agent_name_one, agent_name_two)

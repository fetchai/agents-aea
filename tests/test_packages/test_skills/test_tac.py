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

from tests.test_packages.tools_for_testing import AeaTestCase


class TestTacSkills(AeaTestCase):
    """Test that tac skills work."""

    def test_tac(self, pytestconfig):
        """Run the tac skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        agent_name_one = "tac_participant_one"
        agent_name_two = "tac_participant_two"

        # create agent one and agent two
        self.create_agents(agent_name_one, agent_name_two)

        # prepare two agents for test
        agent_one_dir_path = os.path.join(self.t, agent_name_one)
        agent_two_dir_path = os.path.join(self.t, agent_name_two)

        for agent_path in (agent_one_dir_path, agent_two_dir_path):
            os.chdir(agent_path)

            self.add_item("connection", "fetchai/oef:0.1.0")
            self.add_item("skill", "fetchai/tac_participation:0.1.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.1.0")
            self.disable_ledger_tx("fetchai", "skill", "tac_participation")
            self.disable_ledger_tx("fetchai", "skill", "tac_negotiation")

            self.run_install()

        try:
            os.chdir(agent_one_dir_path)
            process_one = self.run_oef_subprocess()

            os.chdir(agent_two_dir_path)
            process_two = self.run_oef_subprocess()

            time.sleep(10.0)
            process_one.send_signal(signal.SIGINT)
            process_one.wait(timeout=10)
            process_two.send_signal(signal.SIGINT)
            process_two.wait(timeout=10)

            assert process_one.returncode == 0
            assert process_two.returncode == 0
        finally:
            poll_one = process_one.poll()
            if poll_one is None:
                process_one.terminate()
                process_one.wait(2)

            poll_two = process_two.poll()
            if poll_two is None:
                process_two.terminate()
                process_two.wait(2)

        os.chdir(self.t)
        self.delete_agents(agent_name_one, agent_name_two)

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

"""This test module contains the integration test for the gym skill."""

import os
import shutil
import time

from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEATestCaseEmpty

from ...conftest import ROOT_DIR


class TestGymSkill(AEATestCaseEmpty):
    """Test that gym skill works."""

    @skip_test_ci
    def test_gym(self, pytestconfig):
        """Run the gym skill sequence."""
        self.add_item("skill", "fetchai/gym:0.1.0")
        self.add_item("connection", "fetchai/gym:0.1.0")
        self.run_install()

        # add gyms folder from examples
        gyms_src = os.path.join(ROOT_DIR, "examples", "gym_ex", "gyms")
        gyms_dst = os.path.join(self.agent_name, "gyms")
        shutil.copytree(gyms_src, gyms_dst)

        # change config file of gym connection
        file_src = os.path.join(ROOT_DIR, "tests", "data", "gym-connection.yaml")
        file_dst = os.path.join(
            self.agent_name,
            "vendor",
            "fetchai",
            "connections",
            "gym",
            "connection.yaml",
        )
        shutil.copyfile(file_src, file_dst)

        # change number of training steps
        setting_path = "vendor.{}.skills.gym.handlers.gym.args.nb_steps".format(
            FETCHAI_NAME
        )
        self.set_config(setting_path, 20)

        gym_aea_process = self.run_agent("--connections", "fetchai/gym:0.1.0")
        time.sleep(10.0)

        self.terminate_agents(gym_aea_process)

        assert self.is_successfully_terminated(), "Gym test not successful."

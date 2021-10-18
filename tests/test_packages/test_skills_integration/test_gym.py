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

from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import ROOT_DIR


class TestGymSkill(AEATestCaseEmpty):
    """Test that gym skill works."""

    def test_gym(self):
        """Run the gym skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("skill", "fetchai/gym:0.20.0")
        self.run_install()

        # change default connection
        setting_path = "agent.default_connection"
        self.set_config(setting_path, "fetchai/gym:0.19.0")

        diff = self.difference_to_fetched_agent(
            "fetchai/gym_aea:0.25.0", self.agent_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # change connection config
        setting_path = "vendor.fetchai.connections.gym.config.env"
        self.set_config(setting_path, "gyms.env.BanditNArmedRandom")

        # add gyms folder from examples
        gyms_src = os.path.join(ROOT_DIR, "examples", "gym_ex", "gyms")
        gyms_dst = os.path.join(self.agent_name, "gyms")
        shutil.copytree(gyms_src, gyms_dst)

        # change number of training steps
        setting_path = "vendor.fetchai.skills.gym.handlers.gym.args.nb_steps"
        self.set_config(setting_path, 20, "int")

        gym_aea_process = self.run_agent()

        check_strings = (
            "Training starting ...",
            "Training finished. You can exit now via CTRL+C.",
        )
        missing_strings = self.missing_from_output(gym_aea_process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "Gym agent wasn't successfully terminated."

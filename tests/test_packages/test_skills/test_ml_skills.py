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
import sys
import time

import pytest

from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEAWithOefTestCase


class TestMLSkills(AEAWithOefTestCase):
    """Test that ml skills work."""

    @pytest.mark.skipif(
        sys.version_info > (3, 7),
        reason="cannot run on 3.8 as tensorflow not installable",
    )
    @skip_test_ci
    def test_ml_skills(self, pytestconfig):
        """Run the ml skills sequence."""
        self.initialize_aea()
        self.add_scripts_folder()

        data_provider_aea_name = "ml_data_provider"
        model_trainer_aea_name = "ml_model_trainer"
        self.create_agents(data_provider_aea_name, model_trainer_aea_name)

        # prepare data provider agent
        data_provider_aea_dir_path = os.path.join(self.t, data_provider_aea_name)
        os.chdir(data_provider_aea_dir_path)

        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_data_provider:0.1.0")
        self.run_install()

        # prepare model trainer agent
        model_trainer_aea_dir_path = os.path.join(self.t, model_trainer_aea_name)
        os.chdir(model_trainer_aea_dir_path)

        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/ml_train:0.1.0")
        self.run_install()

        os.chdir(data_provider_aea_dir_path)
        data_provider_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(model_trainer_aea_dir_path)
        model_trainer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_tty_read_thread(data_provider_aea_process)
        self.start_error_read_thread(data_provider_aea_process)
        self.start_tty_read_thread(model_trainer_aea_process)
        self.start_error_read_thread(model_trainer_aea_process)

        time.sleep(60)

        data_provider_aea_process.send_signal(signal.SIGINT)
        model_trainer_aea_process.send_signal(signal.SIGINT)
        data_provider_aea_process.wait(timeout=60)
        model_trainer_aea_process.wait(timeout=60)

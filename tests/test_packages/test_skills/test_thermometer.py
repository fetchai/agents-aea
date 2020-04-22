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

"""This test module contains the integration test for the thermometer skills."""

import io
import os
import shutil
import signal
import subprocess  # nosec
import sys
import tempfile
import threading
import time

import pytest

from aea.cli import cli
from aea.crypto.fetchai import FETCHAI as FETCHAI_NAME
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.generic import force_set_config
from aea.test_tools.test_cases import AEAWithOefTestCase

from ...conftest import AUTHOR, CLI_LOG_OPTION

class TestThermometerSkill(AEAWithOefTestCase):
    """Test that thermometer skills work."""

    def test_thermometer(self, pytestconfig):
        """Run the thermometer skills sequence."""
        self.initialize_aea()
        self.add_scripts_folder()

        thermometer_aea_name = "my_thermometer"
        thermometer_client_aea_name = "my_thermometer_client"
        self.create_agents(thermometer_aea_name, thermometer_client_aea_name)

        ledger_apis = {FETCHAI_NAME: {"network": "testnet"}}

        # add packages for agent one and run it
        thermometer_aea_dir_path = os.path.join(self.t, thermometer_aea_name)
        os.chdir(thermometer_aea_dir_path)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/thermometer:0.1.0")

        setting_path = "agent.ledger_apis"
        force_set_config(setting_path, ledger_apis)
        setting_path = (
            "vendor.{}.skills.thermometer.models.strategy.args.has_sensor"
            .format(FETCHAI_NAME)
        )
        force_set_config(setting_path, False)

        self.run_install()

        # add packages for agent two and run it
        thermometer_client_aea_dir_path = os.path.join(self.t, thermometer_client_aea_name)
        os.chdir(thermometer_client_aea_dir_path)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/thermometer_client:0.1.0")
        self.run_install()

        setting_path = "agent.ledger_apis"
        force_set_config(setting_path, ledger_apis)

        self.generate_private_key()
        self.add_private_key()
        self.generate_wealth()

        # run AEAs
        os.chdir(thermometer_aea_dir_path)
        thermometer_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        os.chdir(thermometer_client_aea_dir_path)
        thermometer_client_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_tty_read_thread(thermometer_aea_process)
        self.start_error_read_thread(thermometer_aea_process)
        self.start_tty_read_thread(thermometer_client_aea_process)
        self.start_error_read_thread(thermometer_client_aea_process)

        time.sleep(20)
        thermometer_aea_process.send_signal(signal.SIGINT)
        thermometer_client_aea_process.send_signal(signal.SIGINT)

        thermometer_aea_process.wait(timeout=10)
        thermometer_client_aea_process.wait(timeout=10)

        assert thermometer_aea_process.returncode == 0
        assert thermometer_client_aea_process.returncode == 0

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
import pytest
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from ...common.click_testing import CliRunner

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION


class TestWeatherSkills:
    """Test that weather skills work."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name_one = "my_weather_station"
        cls.agent_name_two = "my_weather_client"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_weather(self, pytestconfig):
        """Run the weather skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")
        # add packages folder
        packages_src = os.path.join(self.cwd, 'packages')
        packages_dst = os.path.join(os.getcwd(), 'packages')
        shutil.copytree(packages_src, packages_dst)

        # create agent one and agent two
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name_one], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name_two], standalone_mode=False)
        assert result.exit_code == 0

        # add packages for agent one and run it
        agent_one_dir_path = os.path.join(self.t, self.agent_name_one)
        os.chdir(agent_one_dir_path)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "weather_station"], standalone_mode=False)
        assert result.exit_code == 0

        process_one = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run"
        ],
            stdout=subprocess.PIPE,
            env=os.environ.copy())

        os.chdir(self.t)

        # add packages for agent two and run it
        agent_two_dir_path = os.path.join(self.t, self.agent_name_two)
        os.chdir(agent_two_dir_path)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "weather_client"], standalone_mode=False)
        assert result.exit_code == 0

        process_two = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run"
        ],
            stdout=subprocess.PIPE,
            env=os.environ.copy())

        # check the gym run ends

        time.sleep(20.0)
        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=20)
        process_two.send_signal(signal.SIGINT)
        process_two.wait(timeout=20)

        assert process_one.returncode == 0
        assert process_two.returncode == 0

        poll_one = process_one.poll()
        if poll_one is None:
            process_one.terminate()
            process_one.wait(2)

        poll_two = process_two.poll()
        if poll_two is None:
            process_two.terminate()
            process_two.wait(2)

        os.chdir(self.t)
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", self.agent_name_one], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", self.agent_name_two], standalone_mode=False)
        assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

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
import shutil
import signal
import subprocess  # nosec
import sys
import tempfile
import time

import pytest

from aea.cli import cli

from ...common.click_testing import CliRunner
from ...conftest import AUTHOR, CLI_LOG_OPTION


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
        packages_src = os.path.join(self.cwd, "packages")
        packages_dst = os.path.join(self.t, "packages")
        shutil.copytree(packages_src, packages_dst)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # create agent one and agent two
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", self.agent_name_one],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", self.agent_name_two],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # add packages for agent one and run it
        agent_one_dir_path = os.path.join(self.t, self.agent_name_one)
        os.chdir(agent_one_dir_path)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/oef:0.2.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/oef:0.2.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "skill",
                "fetchai/weather_station:0.1.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # Load the agent yaml file and manually insert the things we need
        yaml_path = os.path.join(
            "vendor", "fetchai", "skills", "weather_station", "skill.yaml"
        )
        file = open(yaml_path, mode="r")

        # read all lines at once
        whole_file = file.read()

        whole_file = whole_file.replace("is_ledger_tx: true", "is_ledger_tx: false")

        # close the file
        file.close()

        with open(yaml_path, "w") as f:
            f.write(whole_file)

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )
        assert result.exit_code == 0

        os.chdir(self.t)

        # add packages for agent two and run it
        agent_two_dir_path = os.path.join(self.t, self.agent_name_two)
        os.chdir(agent_two_dir_path)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/oef:0.2.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "agent.default_connection",
                "fetchai/oef:0.2.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "add",
                "--local",
                "skill",
                "fetchai/weather_client:0.1.0",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # Load the agent yaml file and manually insert the things we need
        yaml_path = os.path.join(
            "vendor", "fetchai", "skills", "weather_client", "skill.yaml"
        )
        file = open(yaml_path, mode="r")

        # read all lines at once
        whole_file = file.read()

        whole_file = whole_file.replace("is_ledger_tx: true", "is_ledger_tx: false")

        # close the file
        file.close()

        with open(yaml_path, "w") as f:
            f.write(whole_file)

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )
        assert result.exit_code == 0

        try:
            os.chdir(agent_one_dir_path)
            process_one = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    "fetchai/oef:0.2.0",
                ],
                stdout=subprocess.PIPE,
                env=os.environ.copy(),
            )
            os.chdir(agent_two_dir_path)
            process_two = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    "fetchai/oef:0.2.0",
                ],
                stdout=subprocess.PIPE,
                env=os.environ.copy(),
            )

            # TODO increase timeout so we are sure they work until the end of negotiation.
            time.sleep(5.0)
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
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "delete", self.agent_name_one], standalone_mode=False
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "delete", self.agent_name_two], standalone_mode=False
        )
        assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

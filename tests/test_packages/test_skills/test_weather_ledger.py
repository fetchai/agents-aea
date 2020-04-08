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

import io
import os
import shutil
import signal
import subprocess  # nosec
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE

from ...common.click_testing import CliRunner
from ...conftest import AUTHOR, CLI_LOG_OPTION


def _read_tty(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        print("stdout: " + line.replace("\n", ""))


def _read_error(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        print("stderr: " + line.replace("\n", ""))


class TestWeatherSkillsFetchaiLedger:
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

        # Add scripts folder
        scripts_src = os.path.join(self.cwd, "scripts")
        scripts_dst = os.path.join(self.t, "scripts")
        shutil.copytree(scripts_src, scripts_dst)

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

        # add fetchai ledger in both configuration files
        find_text = "ledger_apis: {}"
        replace_text = """ledger_apis:
        fetchai:
            network: testnet"""

        agent_one_config = Path(self.agent_name_one, DEFAULT_AEA_CONFIG_FILE)
        agent_one_config_content = agent_one_config.read_text()
        agent_one_config_content = agent_one_config_content.replace(
            find_text, replace_text
        )
        agent_one_config.write_text(agent_one_config_content)

        agent_two_config = Path(self.agent_name_two, DEFAULT_AEA_CONFIG_FILE)
        agent_two_config_content = agent_two_config.read_text()
        agent_two_config_content = agent_two_config_content.replace(
            find_text, replace_text
        )
        agent_two_config.write_text(agent_two_config_content)

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

        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )
        assert result.exit_code == 0

        # Generate the private keys
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-key", "fetchai"], standalone_mode=False
        )
        assert result.exit_code == 0

        # Add the private key
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add-key", "fetchai", "fet_private_key.txt"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        # Add some funds to the weather station
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "generate-wealth", "fetchai"], standalone_mode=False
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
                stderr=subprocess.PIPE,
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
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
            )

            tty_read_thread = threading.Thread(target=_read_tty, args=(process_one,))
            tty_read_thread.start()

            error_read_thread = threading.Thread(
                target=_read_error, args=(process_one,)
            )
            error_read_thread.start()

            tty_read_thread = threading.Thread(target=_read_tty, args=(process_two,))
            tty_read_thread.start()

            error_read_thread = threading.Thread(
                target=_read_error, args=(process_two,)
            )
            error_read_thread.start()

            time.sleep(10)
            process_one.send_signal(signal.SIGINT)
            process_two.send_signal(signal.SIGINT)

            process_one.wait(timeout=10)
            process_two.wait(timeout=10)

            # text1, err1 = process_one.communicate()
            # text2, err2 = process_two.communicate()

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
            tty_read_thread.join()
            error_read_thread.join()

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

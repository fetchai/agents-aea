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

"""This test module contains the tests for the `aea launch` sub-command."""

import os
import shutil
import signal
import subprocess  # nosec
import sys
import tempfile
import time
from pathlib import Path

import pytest

import yaml

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE

from ..common.click_testing import CliRunner
from ..conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH


class TestLaunch:
    """Test that the command 'aea launch <agent_name>' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name_1 = "myagent_1"
        cls.agent_name_2 = "myagent_2"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name_1])
        assert result.exit_code == 0
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name_2])
        assert result.exit_code == 0

    def test_exit_code_equal_to_zero(self, pytestconfig):
        """Assert that the exit code is equal to zero (i.e. success)."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        try:
            process_launch = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "launch",
                    self.agent_name_1,
                    self.agent_name_2,
                ],
                env=os.environ,
                preexec_fn=os.setsid,
            )

            time.sleep(5.0)
            os.killpg(
                os.getpgid(process_launch.pid), signal.SIGINT
            )  # Send the signal to all the process groups
            process_launch.wait(timeout=5.0)
        finally:
            if not process_launch.returncode == 0:
                poll_one = process_launch.poll()
                if poll_one is None:
                    process_launch.terminate()
                    process_launch.wait(2)

        assert process_launch.returncode == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestLaunchWithOneFailingAgent:
    """Test aea launch when there is a failing agent.."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name_1 = "myagent_1"
        cls.agent_name_2 = "myagent_2"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--author", AUTHOR])
        assert result.exit_code == 0
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name_1])
        assert result.exit_code == 0
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name_2])
        assert result.exit_code == 0

        # add the exception skill to agent 2
        os.chdir(cls.agent_name_2)
        shutil.copytree(
            Path(CUR_PATH, "data", "exception_skill"),
            Path(cls.t, cls.agent_name_2, "skills", "exception"),
        )
        config_path = Path(cls.t, cls.agent_name_2, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))
        os.chdir(cls.t)

    def test_exit_code_equal_to_one(self, pytestconfig):
        """Assert that the exit code is equal to one (i.e. generic failure)."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        try:
            process_launch = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "launch",
                    self.agent_name_1,
                    self.agent_name_2,
                ],
                env=os.environ,
                preexec_fn=os.setsid,
            )

            time.sleep(5.0)
            os.killpg(
                os.getpgid(process_launch.pid), signal.SIGINT
            )  # Send the signal to all the process groups
            process_launch.wait(timeout=5.0)
        finally:
            if not process_launch.returncode == 0:
                poll_one = process_launch.poll()
                if poll_one is None:
                    process_launch.terminate()
                    process_launch.wait(2)

        assert process_launch.returncode == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestLaunchWithWrongArguments:
    """Test aea launch when some agent directory does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "launch", "this_agent_does_not_exist"],
            standalone_mode=True,
        )

    def test_exit_code_equal_to_two(self):
        """Assert that the exit code is equal to two (i.e. bad parameters)."""
        assert self.result.exit_code == 2

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

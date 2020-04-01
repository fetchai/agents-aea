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
import signal
import subprocess  # nosec
import sys
import tempfile
import time
from pathlib import Path

import pytest

import yaml

from aea.cli import cli
from aea.configurations.base import SkillConfig

from ...common.click_testing import CliRunner
from ...conftest import AUTHOR, CLI_LOG_OPTION, ROOT_DIR


class TestGymSkill:
    """Test that gym skill works."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "my_gym_agent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_gym(self, pytestconfig):
        """Run the gym skill sequence."""
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

        # create agent
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", self.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        agent_dir_path = os.path.join(self.t, self.agent_name)
        os.chdir(agent_dir_path)

        # add packages and install dependencies
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "skill", "fetchai/gym:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add", "--local", "connection", "fetchai/gym:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )
        assert result.exit_code == 0

        # add gyms folder from examples
        gyms_src = os.path.join(self.cwd, "examples", "gym_ex", "gyms")
        gyms_dst = os.path.join(self.t, self.agent_name, "gyms")
        shutil.copytree(gyms_src, gyms_dst)

        # change config file of gym connection
        file_src = os.path.join(ROOT_DIR, "tests", "data", "gym-connection.yaml")
        file_dst = os.path.join(
            self.t,
            self.agent_name,
            "vendor",
            "fetchai",
            "connections",
            "gym",
            "connection.yaml",
        )
        shutil.copyfile(file_src, file_dst)

        # change number of training steps
        skill_config_path = Path(
            self.t, self.agent_name, "vendor", "fetchai", "skills", "gym", "skill.yaml"
        )
        skill_config = SkillConfig.from_json(yaml.safe_load(open(skill_config_path)))
        skill_config.handlers.read("gym").args["nb_steps"] = 20
        yaml.safe_dump(skill_config.json, open(skill_config_path, "w"))

        try:
            process = subprocess.Popen(  # nosec
                [
                    sys.executable,
                    "-m",
                    "aea.cli",
                    "run",
                    "--connections",
                    "fetchai/gym:0.1.0",
                ],
                stdout=subprocess.PIPE,
                env=os.environ.copy(),
            )
            time.sleep(10.0)

            # TODO: check the run ends properly

        finally:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=5)

            if not process.returncode == 0:
                poll = process.poll()
                if poll is None:
                    process.terminate()
                    process.wait(2)

            os.chdir(self.t)
            result = self.runner.invoke(
                cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False
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

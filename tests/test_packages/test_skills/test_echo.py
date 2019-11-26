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

"""This test module contains the integration test for the echo skill."""

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from ...common.click_testing import CliRunner

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION


class TestEchoSkill:
    """Test that echo skill works."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name = "my_first_agent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_echo(self, pytestconfig):
        """Run the echo skill sequence."""
        # add packages folder
        packages_src = os.path.join(self.cwd, 'packages')
        packages_dst = os.path.join(os.getcwd(), 'packages')
        shutil.copytree(packages_src, packages_dst)

        # create agent
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name], standalone_mode=False)
        assert result.exit_code == 0
        agent_dir_path = os.path.join(self.t, self.agent_name)
        os.chdir(agent_dir_path)

        # add skills
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "echo"], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "stub"], standalone_mode=False)
        assert result.exit_code == 0

        # run the agent
        process = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run",
            "--connection",
            "stub"
        ],
            stdout=subprocess.PIPE,
            env=os.environ.copy())

        # add sending and receiving envelope from input/output files

        time.sleep(10.0)
        process.send_signal(signal.SIGINT)
        process.wait(timeout=20)

        assert process.returncode == 0

        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        os.chdir(self.t)
        self.result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", self.agent_name], standalone_mode=False)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

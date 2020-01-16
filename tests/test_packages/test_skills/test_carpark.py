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
import subprocess
import sys
import tempfile
import threading
import time

import pytest

from aea.cli import cli

from ...common.click_testing import CliRunner
from ...conftest import CLI_LOG_OPTION


def _read_tty(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        print("stdout: " + line.replace("\n", ""))


def _read_error(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        print("stderr: " + line.replace("\n", ""))


class TestCarPark:
    """Test that carpark skills work."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.agent_name_one = "my_carpark_aea"
        cls.agent_name_two = "my_carpark_client_aea"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_carpark(self, pytestconfig):
        """Run the weather skills sequence."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")
        # add packages folder
        packages_src = os.path.join(self.cwd, 'packages')
        packages_dst = os.path.join(os.getcwd(), 'packages')
        shutil.copytree(packages_src, packages_dst)

        # Add scripts folder
        scripts_src = os.path.join(self.cwd, 'scripts')
        scripts_dst = os.path.join(os.getcwd(), 'scripts')
        shutil.copytree(scripts_src, scripts_dst)

        # create agent one and agent two
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name_one], standalone_mode=False)
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "create", self.agent_name_two], standalone_mode=False)
        assert result.exit_code == 0

        # add packages for agent one and run it
        agent_one_dir_path = os.path.join(self.t, self.agent_name_one)
        os.chdir(agent_one_dir_path)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/oef:0.1.0"], standalone_mode=False)
        assert result.exit_code == 0

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "fetchai/carpark_detection:0.1.0"], standalone_mode=False)
        assert result.exit_code == 0

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False)
        assert result.exit_code == 0

        # Load the agent yaml file and manually insert the things we need
        yaml_path = os.path.join("skills", "carpark_detection", "skill.yaml")
        file = open(yaml_path, mode='r')

        # read all lines at once
        whole_file = file.read()

        whole_file = whole_file.replace("db_is_rel_to_cwd: true", "# db_is_rel_to_cwd: true")
        whole_file = whole_file.replace("db_rel_dir: ../temp_files", "# db_rel_dir: ../temp_files")

        # close the file
        file.close()

        with open(yaml_path, 'w') as f:
            f.write(whole_file)

        process_one = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run",
            '--connections',
            'oef'
        ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy())

        os.chdir(self.t)

        # add packages for agent two and run it
        agent_two_dir_path = os.path.join(self.t, self.agent_name_two)
        os.chdir(agent_two_dir_path)

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "connection", "fetchai/oef:0.1.0"], standalone_mode=False)
        assert result.exit_code == 0

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "add", "skill", "fetchai/carpark_client:0.1.0"], standalone_mode=False)
        assert result.exit_code == 0

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False)
        assert result.exit_code == 0

        # Load the agent yaml file and manually insert the things we need
        file = open("aea-config.yaml", mode='r')

        # read all lines at once
        whole_file = file.read()

        # add in the ledger address
        find_text = "ledger_apis: {}"
        replace_text = """ledger_apis:
        fetchai:
            address: alpha.fetch-ai.com
            port: 80"""

        whole_file = whole_file.replace(find_text, replace_text)

        # close the file
        file.close()

        with open("aea-config.yaml", 'w') as f:
            f.write(whole_file)

        # Generate the private keys
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "generate-key", "fetchai"], standalone_mode=False)
        assert result.exit_code == 0

        # Add some funds to the weather station
        os.chdir(os.path.join(scripts_dst, "../"))
        result = subprocess.call(["python", "./scripts/fetchai_wealth_generation.py", "--private-key", os.path.join("./", self.agent_name_two, "fet_private_key.txt"), "--amount", "1000000000", "--addr", "alpha.fetch-ai.com", "--port", "80"])
        assert result == 0

        os.chdir(agent_two_dir_path)
        process_two = subprocess.Popen([
            sys.executable,
            '-m',
            'aea.cli',
            "run",
            '--connections',
            'oef'
        ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy())

        tty_read_thread = threading.Thread(target=_read_tty, args=(process_one, ))
        tty_read_thread.start()

        error_read_thread = threading.Thread(target=_read_error, args=(process_one, ))
        error_read_thread.start()

        tty_read_thread = threading.Thread(target=_read_tty, args=(process_two, ))
        tty_read_thread.start()

        error_read_thread = threading.Thread(target=_read_error, args=(process_two, ))
        error_read_thread.start()

        time.sleep(60)
        process_one.send_signal(signal.SIGINT)
        process_two.send_signal(signal.SIGINT)

        process_one.wait(timeout=60)
        process_two.wait(timeout=60)

        # text1, err1 = process_one.communicate()
        # text2, err2 = process_two.communicate()

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

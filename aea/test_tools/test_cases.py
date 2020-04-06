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

"""This module contains test case classes based on pytest for AEA end-to-end testing."""

import os
import shutil
import subprocess  # nosec
import sys
import tempfile

import pytest

from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.cli import cli
from aea.test_tools.exceptions import AEATestingException

from tests.common.click_testing import CliRunner
from tests.conftest import AUTHOR, CLI_LOG_OPTION


class AeaTestCase:
    """Test case for AEA end-to-end tests."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()

        # add packages folder
        packages_src = os.path.join(cls.cwd, "packages")
        packages_dst = os.path.join(cls.t, "packages")
        shutil.copytree(packages_src, packages_dst)

        os.chdir(cls.t)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

    def disable_ledger_tx(self, vendor_name, item_type, item_name):
        """
        Disable ledger tx by modifying item yaml settings.
        Run from agent's directory and only for item with present strategy is_ledger_tx setting.

        :param vendor_name: str vendor name.
        :param item_type: str item type.
        :param item_name: str item name.

        :return: None
        """
        json_path = "vendor.{}.{}s.{}.models.strategy.args.is_ledger_tx".format(
            vendor_name, item_type, item_name
        )
        self.run_cli_command("config", "set", json_path, False)

    def disable_aea_logging(self):
        """
        Disable AEA logging of specific agent.
        Run from agent's directory.

        :return: None
        """
        # logging_config = {
        #     "disable_existing_loggers": False,
        #     "version": 1,
        #     "loggers": {"aea.echo_skill": {"level": "CRITICAL"}},
        # }
        config_update_dict = {
            "agent.logging_config.disable_existing_loggers": "False",
            "agent.logging_config.version": "1",
        }
        for path, value in config_update_dict.items():
            self.run_cli_command("config", "set", path, value)

    def run_cli_command(self, *args):
        """
        Run AEA CLI command.

        :param args: CLI args

        :return: None
        """
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, *args], standalone_mode=False
        )
        try:
            assert result.exit_code == 0
        except AssertionError:
            raise AEATestingException(
                "Failed to execute AEA CLI command with args {}.\n"
                "Exit code: {}\nException:\n{}".format(
                    args, result.exit_code, result.exception
                )
            )

    def run_oef_subprocess(self):
        """
        Run OEF connection as subprocess.
        Run from agent's directory.

        :param *args: CLI args

        :return: subprocess object.
        """
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--connections",
                "fetchai/oef:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )
        return process

    def initialize_aea(self, author=AUTHOR):
        """
        Initialize AEA locally with author name.

        :return: None
        """
        self.run_cli_command("init", "--local", "--author", author)

    def create_agents(self, *agents_names):
        """
        Create agents in current working directory.

        :param *agents_names: str agent names.

        :return: None
        """
        for name in agents_names:
            self.run_cli_command("create", "--local", name, "--author", "fetchai")

    def delete_agents(self, *agents_names):
        """
        Delete agents in current working directory.

        :param *agents_names: str agent names.

        :return: None
        """
        for name in agents_names:
            self.run_cli_command("delete", name)

    def add_item(self, item_type, public_id):
        """
        Add an item to the agent.
        Run from agent's directory.

        :param item_type: str item type.
        :param item_type: str item type.

        :return: None
        """
        self.run_cli_command("add", "--local", item_type, public_id)

    def run_install(self):
        """
        Execute AEA CLI install command.
        Run from agent's directory.

        :return: None
        """
        self.run_cli_command("install")


class AeaWithOefTestCase(AeaTestCase):
    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

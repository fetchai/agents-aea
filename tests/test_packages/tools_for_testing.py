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

"""This module contains tools for testing the packages."""

import os
import shutil
import subprocess  # nosec
import sys
import tempfile

import pytest

from aea.cli import cli

from tests.common.click_testing import CliRunner
from tests.conftest import CLI_LOG_OPTION


class AeaTestCase:
    """Test case for AEA end-to-end tests."""

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

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

    def run_cli_command(self, *args):
        """
        Run AEA CLI command.

        :param args: CLI args

        :return: None
        """
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, *args], standalone_mode=False
        )
        assert result.exit_code == 0

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
                "fetchai/oef:0.2.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )
        return process

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

    def set_config(self, dotted_path: str, value: str):
        """
        Execute AEA CLI set config command.
        Run from agent's directory.

        :param dotted_path: the dotted path to the config
        :param value: the value to be set
        :return: None
        """
        self.run_cli_command("config", "set", dotted_path, value)

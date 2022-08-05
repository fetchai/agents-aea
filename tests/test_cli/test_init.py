# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This test module contains the tests for the `aea init` sub-command."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION, CliRunner, random_string


class TestDoInit:
    """Test that the command 'aea init'."""

    def setup(self):
        """Set the test up."""
        self.runner = CliRunner()
        self.agent_name = "myagent"
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        self.agent_folder = Path(self.t, self.agent_name)
        os.chdir(self.t)
        self.cli_config_file = f"{self.t}/cli_config.yaml"
        self.cli_config_patch = patch(
            "aea.cli.utils.config.CLI_CONFIG_PATH", self.cli_config_file
        )
        self.cli_config_patch.start()

    def test_author_local(self):
        """Test author set localy."""
        author = "test_author"
        assert not os.path.exists(self.cli_config_file)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--reset", "--local", "--author", author],
        )

        assert result.exit_code == 0
        assert "AEA configurations successfully initialized" in result.output
        assert self._read_config()["author"] == "test_author"

    def _read_config(self) -> dict:
        """Read cli config file.

        :return: dict
        """
        with open(self.cli_config_file, "r") as f:
            data = yaml.safe_load(f)
        return data

    def test_already_registered(self):
        """Test author already registered."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", "author"],
        )
        assert result.exit_code == 0
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "init", "--local"])
        assert "AEA configurations already initialized" in result.output

    @patch("aea.cli.register.register_new_account", return_value="TOKEN")
    def test_non_local(self, mock):
        """Test registration online."""
        email = f"{random_string()}@{random_string()}.com"
        pwd = random_string()
        author = "test_author" + random_string()
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "init",
                "--reset",
                "--author",
                author,
                "--remote",
                "--http",
            ],
            input=f"n\n{email}\n{pwd}\n{pwd}\n\n",
        )
        assert result.exit_code == 0, result.output
        assert "Successfully registered" in result.output

        config = self._read_config()
        assert config["author"] == author
        assert config["auth_token"] == "TOKEN"

    @patch("aea.cli.init.do_login", return_value=None)
    def test_registered(self, *mocks):
        """Test author already registered."""
        author = "test_author" + random_string()
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--author", author, "--remote", "--http"],
            input="y\nsome fake password\n",
        )

        assert result.exit_code == 0

    @patch("aea.cli.init.is_auth_token_present", return_value=True)
    @patch("aea.cli.init.check_is_author_logged_in", return_value=True)
    def test_already_logged_in(self, *mocks):
        """Registered and logged in (has token)."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--author", "test_author"],
        )
        assert result.exit_code == 0

    def teardown(self):
        """Tear the test down."""
        self.cli_config_patch.stop()
        os.chdir(self.cwd)
        shutil.rmtree(self.t)

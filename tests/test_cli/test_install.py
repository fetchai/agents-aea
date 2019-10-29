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

"""This test module contains the tests for the `aea install` sub-command."""
import os
import tempfile
import unittest.mock
from pathlib import Path

import yaml
from click.testing import CliRunner

import aea.cli.common
from aea.cli import cli
from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE
from tests.conftest import CLI_LOG_OPTION, CUR_PATH


class TestInstall:
    """Test that the command 'aea install' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        os.chdir(Path(CUR_PATH, "data", "dummy_aea"))
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "install"])

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)


class TestInstallFromRequirementFile:
    """Test that the command 'aea install --requirement REQ_FILE' works."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        os.chdir(Path(CUR_PATH, "data", "dummy_aea"))

        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "install", "-r", "requirements.txt"])

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)


class TestInstallFails:
    """Test that the command 'aea install' fails when a dependency is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"

        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "scaffold", "protocol", "my_protocol"])
        assert result.exit_code == 0

        config_path = Path("protocols", "my_protocol", DEFAULT_PROTOCOL_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("dependencies", []).append("this_dependency_does_not_exist")
        yaml.safe_dump(config, open(config_path, "w"))
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "install"])

    def test_exit_code_equal_to_minus_1(self):
        """Assert that the exit code is equal to -1 (i.e. failure)."""
        assert self.result.exit_code == -1

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)

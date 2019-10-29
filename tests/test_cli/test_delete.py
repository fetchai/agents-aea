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

"""This test module contains the tests for the `aea delete` sub-command."""
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

from click.testing import CliRunner

import aea
import aea.cli.common
from aea.cli import cli
from tests.conftest import CLI_LOG_OPTION


class TestDelete:
    """Test that the command 'aea create <agent_name>' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", cls.agent_name])

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    def test_agent_directory_path_does_not_exists(self):
        """Check that the agent's directory has been deleted."""
        agent_dir = Path(self.agent_name)
        assert not agent_dir.exists()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestDeleteFailsWhenDirectoryDoesNotExist:
    """Test that 'aea delete' sub-command fails when the directory with the agent name in input does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        # agent's directory does not exist -> command will fail.
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", cls.agent_name])

    def test_exit_code_equal_to_2(self):
        """Test that the error code is equal to 2 (i.e. Misuse of shell builtins)"""
        assert self.result.exit_code == 2

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestDeleteFailsWhenDirectoryIsNotAnAEAProject:
    """Test that 'aea delete' sub-command fails when the directory with the agent name in input is not an AEA project."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()

        # directory is not AEA project -> command will fail.
        Path(cls.t, cls.agent_name).mkdir()
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "delete", cls.agent_name])

    def test_exit_code_equal_to_1(self):
        """Test that the error code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    def test_log_error_message(self):
        """Test that the log error message is fixed.

        The expected message is: 'Directory already exist. Aborting...'
        """
        s = "The name provided is not an AEA project."
        self.mocked_logger_error.assert_called_once_with(s)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.patch.__exit__()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

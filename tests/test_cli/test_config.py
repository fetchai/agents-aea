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

"""This test module contains the tests for the `aea config` sub-command."""
import os
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import aea.cli.common
from aea.cli import cli
from tests.conftest import CLI_LOG_OPTION, CUR_PATH
from ..common.click_testing import CliRunner


class TestConfigGet:
    """Test that the command 'aea config get' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        os.chdir(Path(cls.t, "dummy_aea"))

        cls.patch = unittest.mock.patch.object(aea.cli.common.logger, 'error')
        cls.mocked_logger_error = cls.patch.__enter__()
        cls.runner = CliRunner()

    def test_get_agent_name(self):
        """Test getting the agent name."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "agent.agent_name"], standalone_mode=False)
        assert result.exit_code == 0
        assert result.output == "Agent0\n"

    def test_get_skill_name(self):
        """Test getting the 'dummy' skill name."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "skills.dummy.name"], standalone_mode=False)
        assert result.exit_code == 0
        assert result.output == "dummy\n"

    def test_no_recognized_root(self):
        """Test that the 'get' fails because the root is not recognized."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "wrong_root.agent_name"], standalone_mode=False)
        assert result.exit_code == 1
        assert result.exception.message == "The root of the dotted path must be one of: ['agent', 'skills', 'protocols', 'connections']"

    def test_too_short_path_but_root_correct(self):
        """Test that the 'get' fails because the path is too short but the root is correct."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "agent"], standalone_mode=False)
        assert result.exit_code == 1
        assert result.exception.message == "The path is too short. Please specify a path up to an attribute name."

        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "skills.dummy"], standalone_mode=False)
        assert result.exit_code == 1
        assert result.exception.message == "The path is too short. Please specify a path up to an attribute name."

    def test_resource_not_existing(self):
        """Test that the 'get' fails because the resource does not exist."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "connections.non_existing_connection.name"], standalone_mode=False)
        assert result.exit_code == 1
        assert result.exception.message == "Resource connections/non_existing_connection does not exist."

    def test_attribute_not_found(self):
        """Test that the 'get' fails because the attribute is not found."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "skills.dummy.non_existing_attribute"], standalone_mode=False)
        assert result.exit_code == 1
        self.mocked_logger_error.assert_called_with("Attribute not found.")

    def test_get_fails_when_getting_non_primitive_type(self):
        """Test that getting the 'dummy' skill behaviours fails because not a primitive type."""
        result = self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "get", "skills.dummy.behaviours"],
                                    standalone_mode=False)
        assert result.exit_code == 1
        self.mocked_logger_error.assert_called_with("Attribute is not of primitive type.")

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass

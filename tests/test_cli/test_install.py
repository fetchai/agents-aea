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
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import yaml

from aea.cli import cli
from aea.cli.install import _install_dependency
from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE
from aea.exceptions import AEAException

from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner


class TestInstall:
    """Test that the command 'aea install' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'dummy_aea' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        cls.runner = CliRunner()
        os.chdir(Path(cls.t, "dummy_aea"))
        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestInstallFromRequirementFile:
    """Test that the command 'aea install --requirement REQ_FILE' works."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'dummy_aea' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        cls.runner = CliRunner()
        os.chdir(Path(cls.t, "dummy_aea"))

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "install", "-r", "requirements.txt"],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestInstallFailsWhenDependencyDoesNotExist:
    """Test that the command 'aea install' fails when a dependency is not found."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "create", "--local", cls.agent_name],
            standalone_mode=False,
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "protocol", "my_protocol"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        config_path = Path("protocols", "my_protocol", DEFAULT_PROTOCOL_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("dependencies", {}).update(
            {
                "this_is_a_test_dependency": {
                    "version": "==0.1.0",
                    "index": "https://test.pypi.org/simple",
                },
                "this_is_a_test_dependency_on_git": {
                    "git": "https://github.com/an_user/a_repo.git",
                    "ref": "master",
                },
            }
        )
        yaml.safe_dump(config, open(config_path, "w"))
        cls.result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "install"], standalone_mode=False
        )

    def test_exit_code_equal_to_1(self):
        """Assert that the exit code is equal to 1 (i.e. catchall for general errors)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestInstallWithRequirementFailsWhenFileIsBad:
    """Test that the command 'aea install -r REQ_FILE' fails if the requirement file is not good."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        # copy the 'dummy_aea' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(cls.t, "dummy_aea"))
        cls.runner = CliRunner()
        os.chdir(Path(cls.t, "dummy_aea"))

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "install", "-r", "bad_requirements.txt"],
            standalone_mode=False,
        )

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


@mock.patch("aea.cli.install.subprocess.Popen")
@mock.patch("aea.cli.install.subprocess.Popen.wait")
@mock.patch("aea.cli.install.sys.exit")
class InstallDependencyTestCase(TestCase):
    """Test case for _install_dependency method."""

    def test__install_dependency_with_git_url(self, *mocks):
        """Test for _install_dependency method with git url."""
        dependency = {
            "git": "url",
        }
        with self.assertRaises(AEAException):
            _install_dependency("dependency_name", dependency)

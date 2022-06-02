# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

from pathlib import Path
from typing import Dict

import pytest
import yaml
from click import ClickException

from aea.configurations.base import DEFAULT_PROTOCOL_CONFIG_FILE
from aea.configurations.constants import DEFAULT_CONNECTION_CONFIG_FILE
from aea.test_tools.test_cases import AEATestCase, AEATestCaseEmpty

from tests.conftest import CUR_PATH


class TestInstall(AEATestCase):
    """Test that the command 'aea install' works as expected."""

    path_to_aea: Path = Path(CUR_PATH, "data", "dummy_aea")

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.result = cls.run_cli_command("install", cwd=cls._get_cwd())

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0


class TestInstallFromRequirementFile(AEATestCase):
    """Test that the command 'aea install --requirement REQ_FILE' works."""

    path_to_aea: Path = Path(CUR_PATH, "data", "dummy_aea")

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.result = cls.run_cli_command(
            "install", "-r", "requirements.txt", cwd=cls._get_cwd()
        )

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0


class TestInstallFailsWhenDependencyDoesNotExist(AEATestCaseEmpty):
    """Test that the command 'aea install' fails when a dependency is not found."""

    capture_log = True

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        result = cls.run_cli_command(
            "scaffold", "protocol", "-y", "my_protocol", cwd=cls._get_cwd()
        )
        assert result.exit_code == 0

        config_path = (
            Path(cls._get_cwd())
            / "protocols"
            / "my_protocol"
            / DEFAULT_PROTOCOL_CONFIG_FILE
        )
        with config_path.open() as fp:
            config = yaml.safe_load(fp)

        config.setdefault("dependencies", {}).update(
            {
                "this_is_a_test_dependency": {
                    "version": "==0.1.0",
                    "index": "https://test.pypi.org/simple",
                },
            }
        )

        with config_path.open(mode="w") as fp:
            yaml.safe_dump(config, fp)

    def test_error(self):
        """Assert an error occurs."""
        with pytest.raises(
            ClickException,
            match="An error occurred while installing.*this_is_a_test_dependency.*",
        ):
            self.run_cli_command("install", cwd=self._get_cwd())


class TestInstallWithRequirementFailsWhenFileIsBad(AEATestCase):
    """Test that the command 'aea install -r REQ_FILE' fails if the requirement file is not good."""

    path_to_aea: Path = Path(CUR_PATH, "data", "dummy_aea")

    def test_error(self):
        """Test that an error occurs."""
        with pytest.raises(
            ClickException,
            match="An error occurred while installing requirement file bad_requirements.txt. Stopping...",
        ):
            self.run_cli_command(
                "install", "-r", "bad_requirements.txt", cwd=self._get_cwd()
            )


class TestInstallFailsWhenDependencyHasUnsatisfiableSpecifier(AEATestCaseEmpty):
    """Test that the command 'aea install' fails when a dependency has an unsatisfiable version specifier."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        result = cls.run_cli_command(
            "scaffold", "connection", "my_connection_1", cwd=cls._get_cwd()
        )
        assert result.exit_code == 0
        result = cls.run_cli_command(
            "scaffold", "connection", "my_connection_2", cwd=cls._get_cwd()
        )
        assert result.exit_code == 0

        config_path_1 = (
            Path(cls._get_cwd())
            / "connections"
            / "my_connection_1"
            / DEFAULT_CONNECTION_CONFIG_FILE
        )

        cls._write_dependencies(
            {"this_is_a_test_dependency": {"version": "==0.1.0"}}, config_path_1
        )

        config_path_2 = (
            Path(cls._get_cwd())
            / "connections"
            / "my_connection_2"
            / DEFAULT_CONNECTION_CONFIG_FILE
        )

        cls._write_dependencies(
            {"this_is_a_test_dependency": {"version": "==0.2.0"}}, config_path_2
        )

    @classmethod
    def _write_dependencies(cls, dependency_dict: Dict, path_to_config: Path):
        """Write a dependency to a configuration file."""
        with path_to_config.open() as fp:
            config = yaml.safe_load(fp)
        config.setdefault("dependencies", {}).update(dependency_dict)
        with path_to_config.open(mode="w") as fp:
            yaml.safe_dump(config, fp)

    def test_error(self):
        """Assert an error occurs."""
        with pytest.raises(
            ClickException,
            match="cannot install the following dependencies as the joint version specifier is unsatisfiable:\n - this_is_a_test_dependency: ==0.1.0,==0.2.0",
        ):
            self.run_cli_command("install", cwd=self._get_cwd())

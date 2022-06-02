# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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


"""This test module contains the tests for the `aea build` sub-command."""
import re
from pathlib import Path
from unittest import mock

import pytest
from click.exceptions import ClickException

from aea.configurations.constants import DEFAULT_VERSION
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.common.utils import run_aea_subprocess


class TestAEABuildEmpty(AEATestCaseEmpty):
    """Test the command 'aea build', empty project."""

    def test_build(self):
        """Test build command."""
        result = self.run_cli_command("build", cwd=self._get_cwd())
        assert result.exit_code == 0
        assert "Build completed!" in result.stdout


class TestAEABuildMainEntrypoint(AEATestCaseEmpty):
    """Test the command 'aea build', only main entrypoint."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        super().setup_class()
        cls.entrypoint = "script.py"
        cls.expected_string = "Hello, world!"
        (Path(cls._get_cwd()) / cls.entrypoint).write_text(
            f"print('{cls.expected_string}')"
        )
        cls.nested_set_config("agent.build_entrypoint", cls.entrypoint)

    def test_build(self):
        """Test build command."""
        result, stdout, stderr = run_aea_subprocess("-s", "build", cwd=self._get_cwd())
        assert result.returncode == 0
        assert re.search(r"Building AEA package\.\.\.", stdout)
        assert re.search(r"Running command '.*script\.py .+'", stdout)
        assert "Build completed!" in stdout
        assert self.expected_string in stdout


class TestAEABuildPackageEntrypoint(AEATestCaseEmpty):
    """Test the command 'aea build', with a package entrypoint."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        super().setup_class()
        cls.entrypoint = "script.py"
        cls.expected_string = "Hello, world!"
        cls.scaffold_package_name = "my_protocol"
        cls.scaffold_item("protocol", cls.scaffold_package_name)
        (
            Path(cls._get_cwd())
            / "protocols"
            / cls.scaffold_package_name
            / cls.entrypoint
        ).write_text(f"print('{cls.expected_string}')")
        cls.nested_set_config(
            f"protocols.{cls.scaffold_package_name}.build_entrypoint", cls.entrypoint
        )

    def test_build(self):
        """Test build command."""
        result, stdout, stderr = run_aea_subprocess("-s", "build", cwd=self._get_cwd())
        assert result.returncode == 0
        assert re.search(
            rf"Building package \(protocol, {self.author}/{self.scaffold_package_name}:{DEFAULT_VERSION}\)...",
            stdout,
        )
        assert re.search(r"Running command '.*script\.py .+'", stdout)
        assert "Build completed!" in stdout


class TestAEABuildEntrypointNegative(AEATestCaseEmpty):
    """Test the command 'aea build', in case there is an exception."""

    @mock.patch(
        "aea.cli.build.AEABuilder.call_all_build_entrypoints",
        side_effect=Exception("some error."),
    )
    def test_build_exception(self, *_mock):
        """Test build exception."""
        with pytest.raises(ClickException, match="some error."):
            self.run_cli_command("build", cwd=self._get_cwd())

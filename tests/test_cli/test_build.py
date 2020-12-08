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

"""This test module contains the tests for the `aea build` sub-command."""
import re
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Tuple

from aea.configurations.constants import DEFAULT_VERSION
from aea.test_tools.test_cases import AEATestCaseEmpty


class BaseTestAEABuild(AEATestCaseEmpty):
    """Base test class for AEA."""

    def run_aea_subprocess(self, *args) -> Tuple[subprocess.Popen, str, str]:
        """
        Run subprocess, bypassing ClickRunner.invoke.

        The reason is that for some reason ClickRunner.invoke doesn't capture
        well the stdout/stderr of nephew processes - childrne processes of children processes.
        """
        result = subprocess.Popen(  # type: ignore  # nosec
            [sys.executable, "-m", "aea.cli", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._get_cwd(),
            text=True,
        )
        result.wait()
        stdout, stderr = result.communicate()
        return result, stdout, stderr


class TestAEABuildEmpty(AEATestCaseEmpty):
    """Test the command 'aea build', empty project."""

    def test_build(self):
        """Test build command."""
        result = self.run_cli_command("build", cwd=self._get_cwd())
        assert result.exit_code == 0
        assert "Build completed!\n" == result.stdout


class TestAEABuildMainEntrypoint(BaseTestAEABuild):
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
        result, stdout, stderr = self.run_aea_subprocess("-s", "build")
        assert result.returncode == 0
        assert re.search("^Building AEA package...", stdout)
        assert re.search(r"Running command .*python script\.py", stdout)
        assert "\nBuild completed!\n" in stdout
        assert self.expected_string in stdout


class TestAEABuildPackageEntrypoint(BaseTestAEABuild):
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
        result, stdout, stderr = self.run_aea_subprocess("-s", "build")
        assert result.returncode == 0
        assert re.search(
            rf"^Building package \(protocol, {self.author}/{self.scaffold_package_name}:{DEFAULT_VERSION}\)...",
            stdout,
        )
        assert re.search(r"Running command .*python script\.py", stdout)
        assert "\nBuild completed!\n" in stdout

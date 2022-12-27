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
"""This module contains a test for aea.test_tools."""

import os
from pathlib import Path
from typing import cast
from unittest.mock import patch

import click
import pytest
from _pytest.capture import CaptureFixture  # type: ignore

import aea
from aea.cli.core import cli
from aea.test_tools.click_testing import CliRunner, CliTest
from aea.test_tools.utils import copy_class


def test_invoke():
    """Test runner invoke method."""
    cli_runner = CliRunner()

    result = cli_runner.invoke(cli, ["--help"])
    assert (
        "Command-line tool for setting up an Autonomous Economic Agent" in result.output
    )

    result = cli_runner.invoke(cli, "--help")
    assert (
        "Command-line tool for setting up an Autonomous Economic Agent" in result.output
    )


def test_invoke_error():
    """Test runner invoke method raises an error."""
    cli_runner = CliRunner()

    with patch.object(cli, "main", side_effect=SystemExit(1)):
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 1

    with patch.object(cli, "main", side_effect=SystemExit(object())):
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 1


def test_catch_exception():
    """Test runner invoke method raises an exception and its propogated."""
    cli_runner = CliRunner()

    # True
    with patch.object(cli, "main", side_effect=ValueError("expected")):
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 1

    # False
    with pytest.raises(ValueError, match="expected"):
        with patch.object(cli, "main", side_effect=ValueError("expected")):
            cli_runner.invoke(cli, ["--help"], catch_exceptions=False)


def test_mix_std_err_False():
    """Test stderr and stdout not mixed."""
    cli_runner = CliRunner(mix_stderr=False)

    result = cli_runner.invoke(cli, "-v DEBUG run")
    assert result.exit_code == 1
    # check for access, no exception should be raised
    assert result.stderr is not None


def test_mix_std_err_True():
    """Test stderr and stdout are mixed."""
    cli_runner = CliRunner(mix_stderr=True)

    result = cli_runner.invoke(cli, "-v DEBUG run")
    assert result.exit_code == 1

    with pytest.raises(ValueError, match="stderr not separately captured"):
        assert result.stderr


def test_click_version():
    """Test click version"""

    message = """
    When this tests fails you need to ensure that the current versions implementation
    of the click.testing.CliRunner remains compatible with our monkey-patched version
    """
    assert click.__version__ == "8.0.2", message


@pytest.mark.parametrize("mix_stderr", [True, False])
def test_capfd_on_cli_runner(mix_stderr: bool, capfd: CaptureFixture):
    """Test setting capfd on CliRunner to redirect streams"""

    def run_cli_command_and_assert() -> None:
        result = cli_runner.invoke(cli, ["--help"], standalone_mode=False)
        expected = "Command-line tool for setting up an Autonomous Economic Agent"
        assert expected in result.stdout
        if mix_stderr:
            with pytest.raises(ValueError, match="stderr not separately captured"):
                assert result.stderr

    cli_runner = CliRunner(mix_stderr=mix_stderr)

    with patch.object(capfd, "readouterr", wraps=capfd.readouterr) as m:

        # streams captured via CliRunner.isolation context manager
        run_cli_command_and_assert()
        m.assert_not_called()

        # streams captured via pytest capfd fixture
        cli_runner.capfd = capfd
        run_cli_command_and_assert()
        m.assert_called_once()


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(input="input"),
        dict(env={"key": "value"}),
        dict(color=True),
    ],
)
def test_cli_runner_invoke_raises(kwargs, capfd: CaptureFixture):
    """Test CliRunner with capfd raises"""

    cli_runner = CliRunner()
    cli_runner.capfd = capfd
    with pytest.raises(
        NotImplementedError,
        match="Cannot use capfd in conjunction with `input`, `env` or `color`.",
    ):
        cli_runner.invoke(cli, ["--help"], standalone_mode=False, **kwargs)


class TestCliTest:
    """Test CliTest"""

    def setup(self) -> None:
        """Setup test"""
        # `copy` the class to avoid test interference
        self.test_cls = cast(CliTest, copy_class(CliTest))

    def setup_test(self) -> CliTest:
        """Setup test"""

        self.test_cls.setup_class()
        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        return test_instance

    def test_setup_cls_and_setup(self) -> None:
        """Test setup_class and setup"""

        self.test_cls.setup_class()
        assert isinstance(self.test_cls._CliTest__cli_runner, CliRunner)  # type: ignore
        assert self.test_cls._CliTest__cli.name == "aea"  # type: ignore
        assert not hasattr(self.test_cls, "_t")

        test_instance = self.test_cls()  # type: ignore
        test_instance.setup()
        assert isinstance(test_instance._t, Path)

    def test_teardown_and_teardown_cls(self) -> None:
        """Test teardown and teardown_class"""

        test_instance = self.setup_test()
        cwd = Path.cwd()

        assert not test_instance._t == cwd
        os.chdir(test_instance._t)
        assert test_instance._t == Path.cwd()
        test_instance.teardown()
        assert not hasattr(self.test_cls, "_t")

        test_instance.teardown_class()
        assert Path.cwd() == cwd

    def test_run_cli(self) -> None:
        """Test run_cli"""

        test_instance = self.setup_test()
        result = test_instance.run_cli("--version")
        assert result.exit_code == 0
        assert f"aea, version {aea.__version__}" in result.stdout

    def test_run_cli_subprocess(self) -> None:
        """Test run_cli_subprocess"""

        test_instance = self.setup_test()
        result = test_instance.run_cli_subprocess("--version")
        assert result.exit_code == 0
        assert f"aea, version {aea.__version__}" in result.stdout

    def test_run_cli_failure(self) -> None:
        """Test run_cli failure"""

        test_instance = self.setup_test()
        result = test_instance.run_cli("non-existent-command")
        assert result.exit_code == 2
        assert "No such command 'non-existent-command'" in result.stdout

    def test_run_cli_subprocess_failure(self) -> None:
        """Test run_cli_subprocess failure"""

        test_instance = self.setup_test()
        result = test_instance.run_cli_subprocess("non-existent-command")
        assert result.exit_code == 2
        assert "No such command 'non-existent-command'" in result.output

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

from unittest.mock import patch

import click
import pytest
from _pytest.capture import CaptureFixture
from aea.cli.core import cli
from aea.test_tools.click_testing import CliRunner


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
    assert result.stderr


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


def test_capfd_on_cli_runner(capfd: CaptureFixture):
    """Test setting capfd on CliRunner to redirect streams"""

    def run_cli_command_and_assert() -> None:
        result = cli_runner.invoke(cli, ["--help"], standalone_mode=False)
        expected = "Command-line tool for setting up an Autonomous Economic Agent"
        assert expected in result.stdout

    cli_runner = CliRunner()

    with patch.object(capfd, "readouterr", wraps=capfd.readouterr) as m:

        # streams captured via CliRunner.isolation context manager
        run_cli_command_and_assert()
        m.assert_not_called()

        # streams captured via pytest capfd fixture
        cli_runner.capfd = capfd
        run_cli_command_and_assert()
        m.assert_called_once()

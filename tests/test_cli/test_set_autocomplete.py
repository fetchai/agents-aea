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
"""This test module contains the tests for the `aea add-key` sub-command."""
from os import environ
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from aea.cli import cli
from aea.cli.set_autocomplete import COMPLETETION_LOAD_CMD, SHELL_SUPPORTED

from tests.conftest import CLI_LOG_OPTION, CliRunner


def test_set_autocomplete():
    """Test set autocomplete command"""
    runner = CliRunner()
    shell = environ.get("SHELL", "/bin/UNKNOWN").split("/")[-1]

    if shell != SHELL_SUPPORTED:
        return

    with patch("aea.cli.set_autocomplete.SHELL_SUPPORTED", "someothershell"):
        result = runner.invoke(
            cli, [*CLI_LOG_OPTION, "set-autocomplete"], catch_exceptions=False
        )
        assert result.exit_code == 1
        assert "is not supported!" in result.stdout

    with NamedTemporaryFile() as bashrc, NamedTemporaryFile() as autocomplete_source:
        with patch("aea.cli.set_autocomplete.BASHRC", bashrc.name), patch(
            "aea.cli.set_autocomplete.AUTOCOMPLETE_FILE_PATH", autocomplete_source.name
        ):
            result = runner.invoke(
                cli, [*CLI_LOG_OPTION, "set-autocomplete"], catch_exceptions=False
            )
            assert result.exit_code == 0, result.stdout
            assert COMPLETETION_LOAD_CMD in str(bashrc.file.read())
            assert autocomplete_source.file.read()

            result = runner.invoke(
                cli, [*CLI_LOG_OPTION, "set-autocomplete"], catch_exceptions=False
            )
            assert "was already updated! skip." in result.stdout

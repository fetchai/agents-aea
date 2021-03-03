# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This test module contains the tests for CLI scaffold generic methods and commands."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli import cli
from aea.cli.scaffold import _scaffold_error_handler

from tests.conftest import CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("aea.cli.scaffold._scaffold_error_handler")
@mock.patch("aea.cli.utils.decorators._check_aea_project")
class ScaffoldErrorHandlerTestCase(TestCase):
    """Test case for CLI scaffold error handler command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_scaffold_error_handler_command_positive(self, *mocks):
        """Test for CLI scaffold error handler command for positive result."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "scaffold", "error-handler"], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


def _raise_exception(*args):
    raise Exception()


class ScaffoldErrHandlerTestCase(TestCase):
    """Test case for _scaffold_error_handler method."""

    def test__scaffold_error_handler_already_exists(self):
        """Test _scaffold_error_handler method dm handler already exists result."""
        err_handler = {"err": "handler"}
        ctx = ContextMock()
        ctx.agent_config.error_handler = err_handler
        with self.assertRaises(ClickException) as cm:
            _scaffold_error_handler(ctx)
        self.assertEqual(
            "A error handler specification already exists. Aborting...",
            str(cm.exception),
        )

    @mock.patch("aea.cli.scaffold.shutil.copyfile", _raise_exception)
    @mock.patch("aea.cli.scaffold.os.remove")
    def test__scaffold_error_handler_exception(self, os_remove_mock, *mocks):
        """Test _scaffold_error_handler method exception raised result."""
        err_handler = {}
        ctx = ContextMock()
        ctx.agent_config.error_handler = err_handler
        with self.assertRaises(ClickException):
            _scaffold_error_handler(ctx)
        os_remove_mock.assert_called_once()

    @mock.patch("aea.cli.scaffold.shutil.copyfile")
    @mock.patch("aea.cli.scaffold.os.remove")
    @mock.patch("aea.cli.scaffold.open_file", mock.mock_open())
    @mock.patch("aea.cli.scaffold.Path", return_value="Path")
    def test__scaffold_error_handler_positive(self, *mocks):
        """Test _scaffold_error_handler method for positive result."""
        err_handler = {}
        ctx = ContextMock()
        ctx.agent_config.error_handler = err_handler
        ctx.agent_loader.dump = mock.Mock()
        _scaffold_error_handler(ctx)
        ctx.agent_loader.dump.assert_called_once()

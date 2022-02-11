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
"""This test module contains the tests for CLI scaffold generic methods and commands."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli import cli
from aea.cli.scaffold import _scaffold_dm_handler

from tests.conftest import CLI_LOG_OPTION, CliRunner
from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("aea.cli.scaffold._scaffold_dm_handler")
@mock.patch("aea.cli.utils.decorators._check_aea_project")
class ScaffoldDecisionMakerHandlerTestCase(TestCase):
    """Test case for CLI scaffold decision maker handler command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_scaffold_decision_maker_handler_command_positive(self, *mocks):
        """Test for CLI scaffold decision maker handler command for positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "decision-maker-handler"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


def _raise_exception(*args):
    raise Exception()


class ScaffoldDmHandlerTestCase(TestCase):
    """Test case for _scaffold_dm_handler method."""

    def test__scaffold_dm_handler_already_exists(self):
        """Test _scaffold_dm_handler method dm handler already exists result."""
        dm_handler = {"dm": "handler"}
        ctx = ContextMock()
        ctx.agent_config.decision_maker_handler = dm_handler
        with self.assertRaises(ClickException) as cm:
            _scaffold_dm_handler(ctx)
        self.assertEqual(
            "A decision maker handler specification already exists. Aborting...",
            str(cm.exception),
        )

    @mock.patch("aea.cli.scaffold.shutil.copyfile", _raise_exception)
    @mock.patch("aea.cli.scaffold.os.remove")
    def test__scaffold_dm_handler_exception(self, os_remove_mock, *mocks):
        """Test _scaffold_dm_handler method exception raised result."""
        dm_handler = {}
        ctx = ContextMock()
        ctx.agent_config.decision_maker_handler = dm_handler
        with self.assertRaises(ClickException):
            _scaffold_dm_handler(ctx)
        os_remove_mock.assert_called_once()

    @mock.patch("aea.cli.scaffold.shutil.copyfile")
    @mock.patch("aea.cli.scaffold.os.remove")
    @mock.patch("aea.cli.scaffold.open_file", mock.mock_open())
    @mock.patch("aea.cli.scaffold.Path", return_value="Path")
    def test__scaffold_dm_handler_positive(self, *mocks):
        """Test _scaffold_dm_handler method for positive result."""
        dm_handler = {}
        ctx = ContextMock()
        ctx.agent_config.decision_maker_handler = dm_handler
        ctx.agent_loader.dump = mock.Mock()
        _scaffold_dm_handler(ctx)
        ctx.agent_loader.dump.assert_called_once()

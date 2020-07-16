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
"""This test module contains the tests for commands in aea.cli.generate_wealth module."""

from unittest import TestCase, mock

from aea.cli import cli
from aea.cli.get_wealth import _try_get_wealth

from tests.conftest import CLI_LOG_OPTION, CliRunner, FETCHAI
from tests.test_cli.tools_for_testing import ContextMock


class GetWealthTestCase(TestCase):
    """Test case for _get_wealth method."""

    @mock.patch("aea.cli.get_wealth.Wallet")
    @mock.patch("aea.cli.get_wealth.verify_or_create_private_keys")
    @mock.patch("aea.cli.get_wealth.try_get_balance")
    def test__get_wealth_positive(self, *mocks):
        """Test for _get_wealth method positive result."""
        ctx = ContextMock()
        _try_get_wealth(ctx, "type")


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.get_wealth.verify_or_create_private_keys")
@mock.patch("aea.cli.get_wealth._try_get_wealth")
@mock.patch("aea.cli.get_wealth.click.echo")
class GetWealthCommandTestCase(TestCase):
    """Test case for CLI get_wealth command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI get_wealth positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "--skip-consistency-check", "get-wealth", FETCHAI],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

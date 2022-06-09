# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

from aea_ledger_fetchai import FetchAICrypto

from aea.cli import cli
from aea.cli.get_wealth import _try_get_wealth
from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import CLI_LOG_OPTION, CliRunner, method_scope
from tests.test_cli.tools_for_testing import ContextMock


class GetWealthTestCase(TestCase):
    """Test case for _get_wealth method."""

    @mock.patch("aea.cli.utils.package_utils.Wallet")
    @mock.patch("aea.cli.utils.package_utils.verify_private_keys_ctx")
    @mock.patch("aea.cli.get_wealth.try_get_balance")
    def test__get_wealth_positive(self, *mocks):
        """Test for _get_wealth method positive result."""
        ctx = ContextMock()
        _try_get_wealth(ctx, "type")


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.utils.package_utils.verify_private_keys_ctx")
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
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "get-wealth",
                FetchAICrypto.identifier,
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@method_scope
class TestGetWealth(AEATestCaseEmpty):
    """Test 'get-wealth' command."""

    @mock.patch("click.echo")
    def test_get_wealth(self, _echo_mock, password_or_none):
        """Run the main test."""
        self.generate_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            password=password_or_none,
        )
        self.add_private_key(
            ledger_api_id=FetchAICrypto.identifier,
            private_key_filepath=PRIVATE_KEY_PATH_SCHEMA.format(
                FetchAICrypto.identifier
            ),
            password=password_or_none,
        )
        self.get_wealth(
            ledger_api_id=FetchAICrypto.identifier, password=password_or_none
        )

        expected_wealth = 0
        _echo_mock.assert_called_with(expected_wealth)

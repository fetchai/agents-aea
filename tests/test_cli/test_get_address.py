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
"""This test module contains the tests for commands in aea.cli.get_address module."""
from unittest import TestCase, mock
from unittest.mock import MagicMock

from aea_ledger_fetchai import FetchAICrypto

from aea.cli import cli
from aea.cli.get_address import _try_get_address
from aea.configurations.constants import DEFAULT_LEDGER
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import CLI_LOG_OPTION, COSMOS_ADDRESS_ONE, CliRunner, method_scope
from tests.test_cli.tools_for_testing import ContextMock


class GetAddressTestCase(TestCase):
    """Test case for _get_address method."""

    @mock.patch(
        "aea.cli.get_address.get_wallet_from_context",
        return_value=MagicMock(addresses={"cosmos": COSMOS_ADDRESS_ONE}),
    )
    def test__get_address_positive(self, *mocks):
        """Test for _get_address method positive result."""
        ctx = ContextMock()
        _try_get_address(ctx, "cosmos")


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.utils.package_utils.verify_private_keys_ctx")
@mock.patch("aea.cli.get_address._try_get_address")
@mock.patch("aea.cli.get_address.click.echo")
class GetAddressCommandTestCase(TestCase):
    """Test case for CLI get_address command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI get_address positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "get-address",
                FetchAICrypto.identifier,
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@method_scope
class TestGetAddressCommand(AEATestCaseEmpty):
    """Test 'get-address' command."""

    def test_get_address(self, password_or_none):
        """Run the main test."""
        self.generate_private_key(password=password_or_none)
        self.add_private_key(password=password_or_none)

        password_option = ["--password", password_or_none] if password_or_none else []
        result = self.run_cli_command(
            "get-address", DEFAULT_LEDGER, *password_option, cwd=self._get_cwd()
        )

        assert result.exit_code == 0

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

"""This test module contains the tests for commands in aea.cli.core module."""
from unittest import TestCase, mock

from aea.cli import cli
from aea.cli.core import (
    _add_key,
    _generate_wealth,
    _get_address,
    _get_wealth,
    _try_get_balance,
    _wait_funds_release,
)
from aea.crypto.fetchai import FETCHAI

from tests.common.click_testing import CliRunner
from tests.conftest import CLI_LOG_OPTION
from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("aea.cli.core._try_get_balance", return_value=0)
@mock.patch("aea.cli.core.FUNDS_RELEASE_TIMEOUT", 0.5)
class WaitFundsReleaseTestCase(TestCase):
    """Test case for _wait_funds_release method."""

    def test__wait_funds_release_positive(self, _try_get_balance_mock):
        """Test for _wait_funds_release method positive result."""
        _wait_funds_release("agent_config", "wallet", "type_")


@mock.patch("aea.cli.core._verify_ledger_apis_access")
@mock.patch("aea.cli.core.LedgerApis", mock.MagicMock())
@mock.patch("aea.cli.core.cast")
class TryGetBalanceTestCase(TestCase):
    """Test case for _try_get_balance method."""

    def test__try_get_balance_positive(
        self, _verify_ledger_apis_access_mock, cast_mock
    ):
        """Test for _try_get_balance method positive result."""
        agent_config = mock.Mock()
        ledger_apis = mock.Mock()
        ledger_apis.read_all = lambda: [["id", "config"], ["id", "config"]]
        agent_config.ledger_apis = ledger_apis

        wallet_mock = mock.Mock()
        wallet_mock.addresses = {"type_": "some-adress"}
        _try_get_balance(agent_config, wallet_mock, "type_")


class GenerateWealthTestCase(TestCase):
    """Test case for _generate_wealth method."""

    @mock.patch("aea.cli.core.Wallet")
    @mock.patch("aea.cli.core.TESTNETS", {"type": "value"})
    @mock.patch("aea.cli.core.click.echo")
    @mock.patch("aea.cli.core._try_generate_testnet_wealth")
    @mock.patch("aea.cli.core._wait_funds_release")
    def test__generate_wealth_positive(self, *mocks):
        """Test for _generate_wealth method positive result."""
        ctx = ContextMock()
        _generate_wealth(ctx, "type", True)


class GetWealthTestCase(TestCase):
    """Test case for _get_wealth method."""

    @mock.patch("aea.cli.core.Wallet")
    @mock.patch("aea.cli.core._try_generate_testnet_wealth")
    @mock.patch("aea.cli.core._try_get_balance")
    def test__get_wealth_positive(self, *mocks):
        """Test for _get_wealth method positive result."""
        ctx = ContextMock()
        _get_wealth(ctx, "type")


class GetAddressTestCase(TestCase):
    """Test case for _get_address method."""

    @mock.patch("aea.cli.core.Wallet")
    def test__get_address_positive(self, *mocks):
        """Test for _get_address method positive result."""
        ctx = ContextMock()
        _get_address(ctx, "type")


@mock.patch("builtins.open", mock.mock_open())
class AddKeyTestCase(TestCase):
    """Test case for _add_key method."""

    def test__add_key_positive(self, *mocks):
        """Test for _add_key method positive result."""
        ctx = ContextMock()
        _add_key(ctx, "type", "filepath")


@mock.patch("aea.cli.core.try_to_load_agent_config")
@mock.patch("aea.cli.core._verify_or_create_private_keys")
@mock.patch("aea.cli.core._generate_wealth")
class GenerateWealthCommandTestCase(TestCase):
    """Test case for CLI generate_wealth command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI generate_wealth positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "generate-wealth", "--sync", FETCHAI],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.core.try_to_load_agent_config")
@mock.patch("aea.cli.core._verify_or_create_private_keys")
@mock.patch("aea.cli.core._get_wealth")
@mock.patch("aea.cli.core.click.echo")
class GetWealthCommandTestCase(TestCase):
    """Test case for CLI get_wealth command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI get_wealth positive result."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "get-wealth", FETCHAI], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.core.try_to_load_agent_config")
@mock.patch("aea.cli.core._verify_or_create_private_keys")
@mock.patch("aea.cli.core._get_address")
@mock.patch("aea.cli.core.click.echo")
class GetAddressCommandTestCase(TestCase):
    """Test case for CLI get_address command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI get_address positive result."""
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "get-address", FETCHAI], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.core.try_to_load_agent_config")
@mock.patch("aea.cli.core._validate_private_key_path")
@mock.patch("aea.cli.core._add_key")
class AddKeyCommandTestCase(TestCase):
    """Test case for CLI add_key command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI add_key positive result."""
        filepath = "setup.py"  # some existing filepath to pass CLI argument check
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "add-key", FETCHAI, filepath], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

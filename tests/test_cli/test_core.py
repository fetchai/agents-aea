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
from pathlib import Path
from unittest import TestCase, mock

import pytest

from aea.cli import cli
from aea.cli.core import (
    _try_add_key,
    _try_generate_wealth,
    _try_get_address,
    _try_get_balance,
    _try_get_wealth,
    _wait_funds_release,
)
from aea.crypto.fetchai import FetchAICrypto
from aea.test_tools.click_testing import CliRunner
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.test_cases import AEATestCaseMany

from tests.conftest import CLI_LOG_OPTION, ROOT_DIR
from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("aea.cli.core._try_get_balance", return_value=0)
@mock.patch("aea.cli.core.FUNDS_RELEASE_TIMEOUT", 0.5)
class WaitFundsReleaseTestCase(TestCase):
    """Test case for _wait_funds_release method."""

    def test__wait_funds_release_positive(self, _try_get_balance_mock):
        """Test for _wait_funds_release method positive result."""
        _wait_funds_release("agent_config", "wallet", "type_")


@mock.patch("aea.cli.core.LedgerApis", mock.MagicMock())
class TryGetBalanceTestCase(TestCase):
    """Test case for _try_get_balance method."""

    def test__try_get_balance_positive(self):
        """Test for _try_get_balance method positive result."""
        agent_config = mock.Mock()
        ledger_apis = {"type_": {"address": "some-adress"}}
        agent_config.ledger_apis_dict = ledger_apis

        wallet_mock = mock.Mock()
        wallet_mock.addresses = {"type_": "some-adress"}
        _try_get_balance(agent_config, wallet_mock, "type_")


class GenerateWealthTestCase(TestCase):
    """Test case for _generate_wealth method."""

    @mock.patch("aea.cli.core.Wallet")
    @mock.patch("aea.cli.core.TESTNETS", {"type": "value"})
    @mock.patch("aea.cli.core.click.echo")
    @mock.patch("aea.cli.core.try_generate_testnet_wealth")
    @mock.patch("aea.cli.core._wait_funds_release")
    def test__generate_wealth_positive(self, *mocks):
        """Test for _generate_wealth method positive result."""
        ctx = ContextMock()
        _try_generate_wealth(ctx, "type", True)


class GetWealthTestCase(TestCase):
    """Test case for _get_wealth method."""

    @mock.patch("aea.cli.core.Wallet")
    @mock.patch("aea.cli.core.try_generate_testnet_wealth")
    @mock.patch("aea.cli.core._try_get_balance")
    def test__get_wealth_positive(self, *mocks):
        """Test for _get_wealth method positive result."""
        ctx = ContextMock()
        _try_get_wealth(ctx, "type")


class GetAddressTestCase(TestCase):
    """Test case for _get_address method."""

    @mock.patch("aea.cli.core.Wallet")
    def test__get_address_positive(self, *mocks):
        """Test for _get_address method positive result."""
        ctx = ContextMock()
        _try_get_address(ctx, "type")


@mock.patch("builtins.open", mock.mock_open())
class AddKeyTestCase(TestCase):
    """Test case for _add_key method."""

    def test__add_key_positive(self, *mocks):
        """Test for _add_key method positive result."""
        ctx = ContextMock()
        _try_add_key(ctx, "type", "filepath")


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.core.verify_or_create_private_keys")
@mock.patch("aea.cli.core._try_generate_wealth")
class GenerateWealthCommandTestCase(TestCase):
    """Test case for CLI generate_wealth command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI generate_wealth positive result."""
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "generate-wealth",
                "--sync",
                FetchAICrypto.identifier,
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.core.verify_or_create_private_keys")
@mock.patch("aea.cli.core._try_get_wealth")
@mock.patch("aea.cli.core.click.echo")
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


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.core.verify_or_create_private_keys")
@mock.patch("aea.cli.core._try_get_address")
@mock.patch("aea.cli.core.click.echo")
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


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.core._try_validate_private_key_path")
@mock.patch("aea.cli.core._try_add_key")
class AddKeyCommandTestCase(TestCase):
    """Test case for CLI add_key command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_run_positive(self, *mocks):
        """Test for CLI add_key positive result."""
        filepath = str(
            Path(ROOT_DIR, "setup.py")
        )  # some existing filepath to pass CLI argument check
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "--skip-consistency-check",
                "add-key",
                FetchAICrypto.identifier,
                filepath,
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)


class TestWealthCommands(AEATestCaseMany):
    """Test case for CLI wealth commands."""

    def test_wealth_commands(self):
        """Test wealth commands."""
        agent_name = "test_aea"
        self.create_agents(agent_name)

        self.set_agent_context(agent_name)
        ledger_apis = {"fetchai": {"network": "testnet"}}
        self.force_set_config("agent.ledger_apis", ledger_apis)

        self.generate_private_key()
        self.add_private_key()

        self.generate_wealth()

        settings = {"unsupported_crypto": "path"}
        self.force_set_config("agent.private_key_paths", settings)
        with pytest.raises(AEATestingException) as excinfo:
            self.generate_wealth()

        assert "Crypto not registered with id 'unsupported_crypto'." in str(
            excinfo.value
        )

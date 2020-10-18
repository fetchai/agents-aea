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
"""This test module contains the tests for commands in aea.cli.get_address module."""

from unittest import TestCase, mock

from aea.cli import cli
from aea.cli.get_address import _try_get_address

from tests.conftest import CLI_LOG_OPTION, CliRunner, FETCHAI
from tests.test_cli.tools_for_testing import ContextMock


class GetAddressTestCase(TestCase):
    """Test case for _get_address method."""

    @mock.patch("aea.cli.utils.package_utils.Wallet")
    @mock.patch("aea.cli.utils.package_utils.verify_or_create_private_keys_ctx")
    def test__get_address_positive(self, *mocks):
        """Test for _get_address method positive result."""
        ctx = ContextMock()
        _try_get_address(ctx, "type")


@mock.patch("aea.cli.utils.decorators.try_to_load_agent_config")
@mock.patch("aea.cli.utils.package_utils.verify_or_create_private_keys_ctx")
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
            [*CLI_LOG_OPTION, "--skip-consistency-check", "get-address", FETCHAI],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)

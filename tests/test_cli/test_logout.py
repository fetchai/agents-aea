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
"""This test module contains the tests for CLI logout command."""

from unittest import TestCase, mock

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION, CliRunner


@mock.patch("aea.cli.logout.registry_logout")
@mock.patch("aea.cli.logout.update_cli_config")
class LogoutTestCase(TestCase):
    """Test case for CLI logout command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_logout_positive(self, update_cli_config_mock, registry_logout_mock):
        """Test for CLI logout positive result."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "logout"],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        registry_logout_mock.assert_called_once()
        update_cli_config_mock.assert_called_once()

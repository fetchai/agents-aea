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
"""This test module contains the tests for CLI login command."""

from unittest import TestCase, mock

from aea.cli import cli

from tests.conftest import CLI_LOG_OPTION, CliRunner


@mock.patch("aea.cli.login.registry_login", return_value="token")
@mock.patch("aea.cli.login.update_cli_config")
class LoginTestCase(TestCase):
    """Test case for CLI login command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_login_positive(self, update_cli_config_mock, registry_login_mock):
        """Test for CLI login positive result."""
        username, password = ("Username", "Password")
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "login", username, "--password={}".format(password)],
            standalone_mode=False,
        )
        expected_output = (
            "Signing in as Username...\n" "Successfully signed in: Username.\n"
        )
        self.assertEqual(result.output, expected_output)
        registry_login_mock.assert_called_once_with(username, password)
        update_cli_config_mock.assert_called_once_with({"auth_token": "token"})

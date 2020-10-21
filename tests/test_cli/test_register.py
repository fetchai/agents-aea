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
"""This test module contains the tests for CLI register command."""

from unittest import TestCase, mock

from aea.cli import cli
from aea.cli.register import do_register
from aea.cli.registry.settings import AUTH_TOKEN_KEY

from tests.conftest import CLI_LOG_OPTION, CliRunner


@mock.patch("aea.cli.register.do_register")
class RegisterTestCase(TestCase):
    """Test case for CLI register command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_register_positive(self, do_register_mock):
        """Test for CLI register positive result."""
        username = "username"
        email = "email@example.com"
        fake_pwd = "fake_pwd"  # nosec

        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "register",
                "--username={}".format(username),
                "--email={}".format(email),
                "--password={}".format(fake_pwd),
                "--confirm_password={}".format(fake_pwd),
                "--no-subscribe",
            ],
            standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        do_register_mock.assert_called_once_with(
            username, email, fake_pwd, fake_pwd, True
        )


@mock.patch("aea.cli.register.validate_author_name", lambda x: x)
@mock.patch("aea.cli.register.register_new_account", return_value="token")
@mock.patch("aea.cli.register.click.echo")
@mock.patch("aea.cli.register.click.confirm", return_value=True)
@mock.patch("aea.cli.register.update_cli_config")
class DoRegisterTestCase(TestCase):
    """Test case for do_register method."""

    def test_do_register_positive(
        self, update_cli_config_mock, confirm_mock, echo_mock, *mocks
    ):
        """Test for do_register method positive result."""
        username = "username"
        email = "email@example.com"
        fake_pwd = "fake_pwd"  # nosec
        no_subscribe = False

        do_register(username, email, fake_pwd, fake_pwd, no_subscribe)
        update_cli_config_mock.assert_called_once_with({AUTH_TOKEN_KEY: "token"})
        confirm_mock.assert_called_once()

    def test_do_register_no_subscribe_true_positive(
        self, update_cli_config_mock, confirm_mock, echo_mock, *mocks
    ):
        """Test for do_register method no_subscribe flag = True positive result."""
        username = "username"
        email = "email@example.com"
        fake_pwd = "fake_pwd"  # nosec
        no_subscribe = True

        do_register(username, email, fake_pwd, fake_pwd, no_subscribe)
        update_cli_config_mock.assert_called_once_with({AUTH_TOKEN_KEY: "token"})
        confirm_mock.assert_not_called()

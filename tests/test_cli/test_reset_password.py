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
"""This test module contains the tests for CLI reset_password command."""

from unittest import TestCase, mock

from aea.cli import cli
from aea.cli.reset_password import _do_password_reset

from tests.conftest import CLI_LOG_OPTION, CliRunner


@mock.patch("aea.cli.reset_password._do_password_reset")
class ResetPasswordTestCase(TestCase):
    """Test case for CLI reset_password command."""

    def setUp(self):
        """Set it up."""
        self.runner = CliRunner()

    def test_reset_password_positive(self, registry_reset_password_mock):
        """Test for CLI reset_password positive result."""
        email = "email@example.com"
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "reset_password", email], standalone_mode=False,
        )
        self.assertEqual(result.exit_code, 0)
        registry_reset_password_mock.assert_called_once_with(email)


class DoPasswordResetTestCase(TestCase):
    """Test case for _do_password_reset method."""

    @mock.patch("aea.cli.reset_password.registry_reset_password")
    @mock.patch("aea.cli.reset_password.click.echo")
    def test__do_password_reset_positive(self, echo_mock, registry_reset_password_mock):
        """Test _do_password_reset for positive result."""
        email = "email@example.com"
        _do_password_reset(email)
        registry_reset_password_mock.assert_called_once_with(email)
        echo_mock.assert_called_once_with(
            "An email with a password reset link was sent to {}".format(email)
        )

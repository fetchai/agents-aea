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
"""This test module contains tests for CLI Registry login methods."""

from unittest import TestCase, mock

from aea.cli.registry.login import registry_login, registry_reset_password


@mock.patch("aea.cli.registry.login.request_api", return_value={"key": "key"})
class RegistryLoginTestCase(TestCase):
    """Test case for registry_login method."""

    def test_registry_login_positive(self, request_api_mock):
        """Test for registry_login method positive result."""
        result = registry_login("username", "password")
        expected_result = "key"
        self.assertEqual(result, expected_result)
        request_api_mock.assert_called_once()


@mock.patch(
    "aea.cli.registry.login.request_api", return_value={"message": "Email was sent."}
)
class RegistryResetPasswordTestCase(TestCase):
    """Test case for registry_reset_password method."""

    def test_registry_reset_password_positive(self, request_api_mock):
        """Test for registry_reset_password method positive result."""
        registry_reset_password("email@example.com")
        request_api_mock.assert_called_once()

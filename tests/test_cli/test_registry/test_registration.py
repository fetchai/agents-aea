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
"""Test module for Registry registration methods."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli.registry.registration import register


class RegistrationTestCase(TestCase):
    """Test case for Registry registration methods."""

    @mock.patch(
        "aea.cli.registry.registration.request_api",
        return_value=({"key": "token"}, 201),
    )
    def test_register_positive(self, *mocks):
        """Test register method positive result."""
        username, email, password = ("username", "email", "password")
        result = register(username, email, password, password)
        expected_result = "token"
        self.assertEqual(result, expected_result)

    @mock.patch(
        "aea.cli.registry.registration.request_api",
        return_value=({"username": "Already exists"}, 400),
    )
    def test_register_negative(self, *mocks):
        """Test register method negative result."""
        username, email, password = ("bad-username", "email", "password")
        with self.assertRaises(ClickException):
            register(username, email, password, password)

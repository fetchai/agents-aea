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

    @mock.patch("aea.cli.registry.registration.request_api", return_value=None)
    def test_register_positive(self, *mocks):
        username, email, password = ('username', 'email', 'password')
        register(username, email, password, password)


    @mock.patch(
        "aea.cli.registry.registration.request_api",
        return_value={
            "username": "Already exists"
        }
    )
    def test_register_negative(self, *mocks):
        username, email, password = ('bad-username', 'email', 'password')
        with self.assertRaises(ClickException):
            register(username, email, password, password)

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
"""This test module contains tests for CLI Registry logout methods."""

from unittest import TestCase, mock

from aea.cli.registry.logout import registry_logout


@mock.patch("aea.cli.registry.logout.request_api")
class RegistryLogoutTestCase(TestCase):
    """Test case for registry_logout method."""

    def test_registry_logout_positive(self, request_api_mock):
        """Test for registry_logout method positive result."""
        registry_logout()
        request_api_mock.assert_called_once()

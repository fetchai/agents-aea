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

"""This test module contains the tests for aea.cli.utils.config module."""


from unittest import TestCase, mock

from aea.cli.utils.config import validate_item_config
from aea.cli.utils.exceptions import AEAConfigException

from tests.test_cli.tools_for_testing import (
    AgentConfigMock,
    ConfigLoaderMock,
    FaultyAgentConfigMock,
)


class ValidateItemConfigTestCase(TestCase):
    """Test case for validate_item_config method."""

    @mock.patch(
        "aea.cli.utils.config.load_item_config",
        return_value=AgentConfigMock(description="Description"),
    )
    @mock.patch(
        "aea.cli.utils.config.ConfigLoaders.from_package_type",
        return_value=ConfigLoaderMock(required_fields=["description"]),
    )
    def test_validate_item_config_positive(self, *mocks):
        """Test validate_item_config for positive result."""
        validate_item_config(item_type="agent", package_path="file/path")

    @mock.patch(
        "aea.cli.utils.config.load_item_config", return_value=FaultyAgentConfigMock(),
    )
    @mock.patch(
        "aea.cli.utils.config.ConfigLoaders.from_package_type",
        return_value=ConfigLoaderMock(required_fields=["description"]),
    )
    def test_validate_item_config_negative(self, *mocks):
        """Test validate_item_config for negative result."""
        with self.assertRaises(AEAConfigException):
            validate_item_config(item_type="agent", package_path="file/path")

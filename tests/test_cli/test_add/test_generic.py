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
"""This test module contains tests for aea.cli.add generic methods."""

from unittest import TestCase, mock

from aea.cli.add import _add_item_deps

from tests.test_cli.tools_for_testing import ContextMock


class AddItemDepsTestCase(TestCase):
    """Test case for _add_item_deps method."""

    @mock.patch("aea.cli.add.add_item")
    def test__add_item_deps_missing_skills_positive(self, add_item_mock):
        """Test _add_item_deps for positive result with missing skills."""
        ctx = ContextMock(skills=[])
        item_config = mock.Mock()
        item_config.protocols = []
        item_config.contracts = []
        item_config.connections = []
        item_config.skills = ["skill-1", "skill-2"]
        _add_item_deps(ctx, "skill", item_config)

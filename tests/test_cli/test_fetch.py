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
"""This test module contains the tests for CLI Registry fetch methods."""

from unittest import mock, TestCase

from aea.cli.fetch import _fetch_agent_locally

from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


@mock.patch('aea.cli.fetch.copy_tree')
@mock.patch('aea.cli.fetch.os.path.join', return_value='joined-path')
@mock.patch(
    'aea.cli.fetch.try_get_item_source_path', return_value='path'
)
class FetchAgentLocallyTestCase(TestCase):
    """Test case for fetch_agent_locally method."""

    def test_fetch_agent_locally_positive(
        self,
        try_get_item_source_path_mock,
        join_mock,
        copy_tree
    ):
        """Test for fetch_agent_locally method positive result."""
        _fetch_agent_locally(ContextMock(), PublicIdMock())
        copy_tree.assert_called_once_with('path', 'joined-path')

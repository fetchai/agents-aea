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
"""Test module for aea.cli.remove.remove_item method."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli.remove import remove_item

from tests.test_cli.tools_for_testing import ContextMock, PublicIdMock


@mock.patch("aea.cli.remove.shutil.rmtree")
@mock.patch("aea.cli.remove.Path.exists", return_value=False)
class RemoveItemTestCase(TestCase):
    """Test case for remove_item method."""

    def test_remove_item_item_folder_not_exists(self, *mocks):
        """Test for save_agent_locally item folder not exists."""
        public_id = PublicIdMock.from_str("author/name:0.1.0")
        with self.assertRaises(ClickException):
            remove_item(ContextMock(protocols=[public_id]), "protocol", public_id)

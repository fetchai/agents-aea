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
import os
from unittest import TestCase, mock

from click import ClickException

import pytest

from aea.cli.remove import remove_item
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    DEFAULT_CONNECTION,
    DEFAULT_PROTOCOL,
    DEFAULT_SKILL,
)
from aea.test_tools.test_cases import AEATestCaseEmpty

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


class TestRemovePackageWithLatestVersion(AEATestCaseEmpty):
    """Test case for remove package with latest version."""

    @pytest.mark.parametrize(
        ["type_", "public_id"],
        [
            ("protocol", DEFAULT_PROTOCOL.to_latest()),
            ("connection", DEFAULT_CONNECTION.to_latest()),
            ("contract", PublicId("fetchai", "erc1155").to_latest()),
            ("skill", DEFAULT_SKILL.to_latest()),
        ],
    )
    def test_remove_pacakge_latest_version(self, type_, public_id):
        """Test remove protocol with latest version."""
        assert public_id.package_version.is_latest
        # we need this because there isn't a default contract
        if type_ == "contract":
            self.add_item("contract", str(public_id))

        # first, check the package is present
        items_path = os.path.join(self.agent_name, "vendor", "fetchai", type_ + "s")
        items_folders = os.listdir(items_path)
        item_name = public_id.name
        assert item_name in items_folders

        # remove the package
        self.run_cli_command(*["remove", type_, str(public_id)], cwd=self._get_cwd())

        # check that the 'aea remove' took effect.
        items_folders = os.listdir(items_path)
        assert item_name not in items_folders

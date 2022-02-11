# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This test module contains tests for CLI Registry add methods."""

import os
from unittest import TestCase, mock

from aea.cli.registry.add import fetch_package
from aea.configurations.base import PublicId


@mock.patch("aea.cli.registry.utils.request_api", return_value={"file": "url"})
@mock.patch("aea.cli.registry.add.download_file", return_value="filepath")
@mock.patch("aea.cli.registry.add.extract")
class FetchPackageTestCase(TestCase):
    """Test case for fetch_package method."""

    def test_fetch_package_positive(
        self, extract_mock, download_file_mock, request_api_mock
    ):
        """Test for fetch_package method positive result."""
        obj_type = "connection"
        public_id = PublicId.from_str("author/name:0.1.0")
        cwd = "cwd"
        dest_path = os.path.join("dest", "path", "package_folder_name")

        fetch_package(obj_type, public_id, cwd, dest_path)
        request_api_mock.assert_called_with(
            "GET", "/connections/author/name/0.1.0", params=None
        )
        download_file_mock.assert_called_once_with("url", "cwd")
        extract_mock.assert_called_once_with("filepath", os.path.join("dest", "path"))

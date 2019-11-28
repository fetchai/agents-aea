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
"""This test module contains the tests for CLI Registry utils."""
from unittest import TestCase, mock

from aea.cli.registry.utils import fetch_package


@mock.patch(
    'aea.cli.registry.utils.split_public_id',
    return_value=['owner', 'name', 'version']
)
@mock.patch(
    'aea.cli.registry.utils.request_api',
    return_value={'file': 'url'}
)
@mock.patch(
    'aea.cli.registry.utils._download_file',
    return_value='filepath'
)
@mock.patch('aea.cli.registry.utils._extract')
class FetchPackageTestCase(TestCase):
    """Test case for fetch_package method."""

    def test_fetch_package_positive(
        self,
        _extract_mock,
        _download_file_mock,
        request_api_mock,
        split_public_id_mock
    ):
        """Test for fetch_package method positive result."""
        obj_type = 'connection'
        public_id = 'owner/name:version'
        cwd = 'cwd'

        fetch_package(obj_type, public_id, cwd)
        split_public_id_mock.assert_called_with(public_id)
        request_api_mock.assert_called_with(
            'GET', '/connections/owner/name/version'
        )
        _download_file_mock.assert_called_with('url', 'cwd')
        _extract_mock.assert_called_with('filepath', 'cwd/connections')

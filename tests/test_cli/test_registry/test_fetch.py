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

from unittest import mock

from aea.cli.registry.fetch import fetch_agent


@mock.patch(
    'aea.cli.registry.fetch.request_api',
    return_value={'file': 'url'}
)
@mock.patch(
    'aea.cli.registry.fetch.download_file',
    return_value='filepath'
)
@mock.patch('aea.cli.registry.fetch.extract')
@mock.patch('aea.cli.registry.fetch.os.getcwd', return_value='cwd')
class TestFetchAgent:
    """Test case for fetch_package method."""

    def test_fetch_agent_positive(
        self,
        getcwd_mock,
        extract_mock,
        download_file_mock,
        request_api_mock,
    ):
        """Test for fetch_agent method positive result."""
        public_id = 'owner/name:0.1.0'

        fetch_agent(public_id)
        request_api_mock.assert_called_with(
            'GET', '/agents/owner/name/0.1.0'
        )
        download_file_mock.assert_called_once_with('url', 'cwd')
        extract_mock.assert_called_once_with('filepath', 'cwd/name')

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
from click import ClickException

from aea.cli.registry.fetch import (
    fetch_agent, _get_agent_source_path, fetch_agent_locally
)


def _raise_exception():
    raise Exception()


@mock.patch(
    'aea.cli.registry.fetch.download_file',
    return_value='filepath'
)
@mock.patch('aea.cli.registry.fetch.extract')
@mock.patch('aea.cli.registry.fetch.os.getcwd', return_value='cwd')
class TestFetchAgent(TestCase):
    """Test case for fetch_package method."""

    @mock.patch(
        'aea.cli.registry.fetch.request_api',
        return_value={
            'file': 'url',
            'connections': [],
            'protocols': [],
            'skills': []
        }
    )
    def test_fetch_agent_positive(
        self,
        request_api_mock,
        getcwd_mock,
        extract_mock,
        download_file_mock,
    ):
        """Test for fetch_agent method positive result."""
        public_id = 'author/name:0.1.0'

        fetch_agent(public_id)
        request_api_mock.assert_called_with(
            'GET', '/agents/author/name/0.1.0'
        )
        download_file_mock.assert_called_once_with('url', 'cwd')
        extract_mock.assert_called_once_with('filepath', 'cwd/name')

    @mock.patch('aea.cli.registry.fetch.fetch_package')
    @mock.patch(
        'aea.cli.registry.fetch.request_api',
        return_value={
            'file': 'url',
            'connections': ['public/id:1.0.0'],
            'protocols': ['public/id:1.0.0'],
            'skills': ['public/id:1.0.0']
        }
    )
    def test_fetch_agent_with_dependencies_positive(
        self,
        request_api_mock,
        fetch_package_mock,
        getcwd_mock,
        extract_mock,
        download_file_mock,
    ):
        """Test for fetch_agent method with dependencies positive result."""
        public_id = 'author/name:0.1.0'

        fetch_agent(public_id)
        request_api_mock.assert_called_with(
            'GET', '/agents/author/name/0.1.0'
        )
        download_file_mock.assert_called_once_with('url', 'cwd')
        extract_mock.assert_called_once_with('filepath', 'cwd/name')
        fetch_package_mock.assert_called()

    @mock.patch('aea.cli.registry.fetch.fetch_package', _raise_exception)
    @mock.patch(
        'aea.cli.registry.fetch.request_api',
        return_value={
            'file': 'url',
            'connections': ['public/id:1.0.0'],
            'protocols': [],
            'skills': []
        }
    )
    @mock.patch('aea.cli.registry.fetch.rmtree')
    def test_fetch_agent_with_dependencies_unable_to_fetch(
        self,
        rmtree_mock,
        request_api_mock,
        fetch_package_mock,
        getcwd_mock,
        extract_mock,
    ):
        """Test for fetch_agent method positive result."""
        public_id = 'author/name:0.1.0'

        with self.assertRaises(ClickException):
            fetch_agent(public_id)

        request_api_mock.assert_called_with(
            'GET', '/agents/author/name/0.1.0'
        )
        extract_mock.assert_not_called()
        fetch_package_mock.assert_called_once()
        rmtree_mock.assert_called_once()


@mock.patch('aea.cli.registry.fetch.os.path.join', return_value='joined-path')
class GetAgentSourcePathTestCase(TestCase):
    """Test case for _get_agent_source_path method."""

    @mock.patch('aea.cli.registry.fetch.os.path.exists', return_value=True)
    def test__get_agent_source_path_positive(self, exists_mock, join_mock):
        """Test for _get_agent_source_path method positive result."""
        result = _get_agent_source_path('agent-name')
        expected_result = 'joined-path'
        self.assertEqual(result, expected_result)

    @mock.patch('aea.cli.registry.fetch.os.path.exists', return_value=False)
    def test__get_agent_source_path_not_exists(self, exists_mock, join_mock):
        """Test for _get_agent_source_path method not exists."""
        with self.assertRaises(ClickException):
            _get_agent_source_path('agent-name')


@mock.patch('aea.cli.registry.fetch.copy_tree')
@mock.patch('aea.cli.registry.fetch.os.path.join', return_value='joined-path')
@mock.patch('aea.cli.registry.fetch.os.getcwd', return_value='cwd')
@mock.patch(
    'aea.cli.registry.fetch._get_agent_source_path', return_value='path'
)
class FetchAgentLocallyTestCase(TestCase):
    """Test case for fetch_agent_locally method."""

    def test_fetch_agent_locally_positive(
        self,
        _get_agent_source_path_mock,
        getcwd_mock,
        join_mock,
        copy_tree
    ):
        """Test for fetch_agent_locally method positive result."""
        fetch_agent_locally('author/name:1.0.0')
        copy_tree.assert_called_once_with('path', 'joined-path')

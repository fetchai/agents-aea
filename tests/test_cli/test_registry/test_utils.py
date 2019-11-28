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
import os

from unittest import TestCase, mock
from click import ClickException

from aea.cli.registry.utils import (
    fetch_package, request_api, split_public_id, _download_file
)
from aea.cli.registry.settings import REGISTRY_API_URL


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
        _download_file_mock.assert_called_once_with('url', 'cwd')
        _extract_mock.assert_called_once_with('filepath', 'cwd/connections')


@mock.patch('aea.cli.registry.utils.requests.request')
class RequestAPITestCase(TestCase):
    """Test case for request_api method."""

    def test_request_api_positive(self, request_mock):
        """Test for fetch_package method positive result."""
        expected_result = {'correct': 'json'}

        resp_mock = mock.Mock()
        resp_mock.json = lambda: expected_result
        resp_mock.status_code = 200
        request_mock.return_value = resp_mock

        result = request_api('GET', '/path')
        request_mock.assert_called_once_with(
            method='GET',
            params=None,
            url=REGISTRY_API_URL + '/path'
        )
        self.assertEqual(result, expected_result)

    def test_request_api_404(self, request_mock):
        """Test for fetch_package method 404 sever response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 404
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api('GET', '/path')

    def test_request_api_403(self, request_mock):
        """Test for fetch_package method not authorized sever response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 403
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api('GET', '/path')

    def test_request_api_unexpected_response(self, request_mock):
        """Test for fetch_package method unexpected sever response."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 500
        request_mock.return_value = resp_mock
        with self.assertRaises(ClickException):
            request_api('GET', '/path')


class SplitPublicIDTestCase(TestCase):
    """Test case for request_api method."""

    def test_split_public_id_positive(self):
        """Test for split_public_id method positive result."""
        public_id = 'owner/name:version'
        expected_result = ['owner', 'name', 'version']
        result = split_public_id(public_id)
        self.assertEqual(result, expected_result)


@mock.patch('aea.cli.registry.utils.requests.get')
class DownloadFileTestCase(TestCase):
    """Test case for _download_file method."""

    @mock.patch('builtins.open', mock.mock_open())
    def test_download_file_positive(self, get_mock):
        """Test for _download_file method positive result."""
        filename = 'filename.tar.gz'
        url = 'url/{}'.format(filename)
        cwd = 'cwd'
        filepath = os.path.join(cwd, filename)

        resp_mock = mock.Mock()
        raw_mock = mock.Mock()
        raw_mock.read = lambda: 'file content'

        resp_mock.raw = raw_mock
        resp_mock.status_code = 200
        get_mock.return_value = resp_mock

        result = _download_file(url, cwd)
        expected_result = filepath
        self.assertEqual(result, expected_result)
        get_mock.assert_called_once_with(url, stream=True)

    def test_download_file_wrong_response(self, get_mock):
        """Test for _download_file method wrong response from file server."""
        resp_mock = mock.Mock()
        resp_mock.status_code = 404
        get_mock.return_value = resp_mock

        with self.assertRaises(ClickException):
            _download_file('url', 'cwd')

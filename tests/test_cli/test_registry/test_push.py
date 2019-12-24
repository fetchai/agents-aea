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
"""Test module for Registry push methods."""

import os

from unittest import TestCase, mock

from click import ClickException

from aea.cli.registry.push import (
    push_item,
    _remove_pycache,
    get_packages_path,
    save_item_locally,
    _get_item_source_path,
    _get_item_target_path
)


@mock.patch('aea.cli.registry.utils._rm_tarfiles')
@mock.patch('aea.cli.registry.push.os.getcwd', return_value='cwd')
@mock.patch('aea.cli.registry.push._compress_dir')
@mock.patch(
    'aea.cli.registry.push.load_yaml',
    return_value={'description': 'some-description', 'version': 'some-version'}
)
@mock.patch(
    'aea.cli.registry.push.request_api', return_value={'public_id': 'public-id'}
)
class PushItemTestCase(TestCase):
    """Test case for push_item method."""

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=True)
    def test_push_item_positive(
        self,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock
    ):
        """Test for push_item positive result."""
        push_item('some-type', 'item-name')
        request_api_mock.assert_called_once_with(
            'POST',
            '/some-types/create',
            data={
                'name': 'item-name',
                'description': 'some-description',
                'version': 'some-version',

            },
            auth=True,
            filepath='cwd/item-name.tar.gz'
        )

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=False)
    def test_push_item_item_not_found(
        self,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock
    ):
        """Test for push_item - item not found."""
        with self.assertRaises(ClickException):
            push_item('some-type', 'item-name')

        request_api_mock.assert_not_called()


@mock.patch('aea.cli.registry.push.shutil.rmtree')
class RemovePycacheTestCase(TestCase):
    """Test case for _remove_pycache method."""

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=True)
    def test_remove_pycache_positive(self, path_exists_mock, rmtree_mock):
        """Test for _remove_pycache positive result."""
        source_dir = 'somedir'
        pycache_path = os.path.join(source_dir, '__pycache__')

        _remove_pycache(source_dir)
        rmtree_mock.assert_called_once_with(pycache_path)

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=False)
    def test_remove_pycache_no_pycache(self, path_exists_mock, rmtree_mock):
        """Test for _remove_pycache if there's no pycache."""
        source_dir = 'somedir'
        _remove_pycache(source_dir)
        rmtree_mock.assert_not_called()


@mock.patch(
    'aea.cli.registry.push.os.path.abspath',
    return_value=('somepath/agents-aea/somefile')
)
@mock.patch(
    'aea.cli.registry.push.os.path.join',
    return_value=('correct-path')
)
class GetPackagesPathTestCase(TestCase):
    """Test case for get_packages_path method."""

    def test_get_packages_path_positive(self, join_mock, _):
        """Test for get_packages_path positive result."""
        result = get_packages_path()
        expected_result = 'correct-path'
        self.assertEqual(result, expected_result)
        join_mock.assert_called_once_with('somepath', 'agents-aea', 'packages')


@mock.patch('aea.cli.registry.push.copy_tree')
@mock.patch('aea.cli.registry.push.os.getcwd', return_value='cwd')
class SaveItemLocallyTestCase(TestCase):
    """Test case for save_item_locally method."""

    @mock.patch(
        'aea.cli.registry.push._get_item_target_path', return_value='target'
    )
    @mock.patch(
        'aea.cli.registry.push._get_item_source_path', return_value='source'
    )
    def test_save_item_locally_positive(
        self,
        _get_item_source_path_mock,
        _get_item_target_path_mock,
        getcwd_mock,
        copy_tree_mock
    ):
        """Test for save_item_locally positive result."""
        item_type = 'skill'
        item_name = 'skill-name'
        save_item_locally(item_type, item_name)
        _get_item_source_path_mock.assert_called_once_with(
            'cwd', 'skills', item_name
        )
        _get_item_target_path_mock.assert_called_once_with('skills', item_name)
        getcwd_mock.assert_called_once()
        copy_tree_mock.assert_called_once_with('source', 'target')


@mock.patch('aea.cli.registry.push.os.path.join', return_value='some-path')
class GetItemSourcePathTestCase(TestCase):
    """Test case for _get_item_source_path method."""

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=True)
    def test__get_item_source_path_positive(self, exists_mock, join_mock):
        """Test for _get_item_source_path positive result."""
        _get_item_source_path('cwd', 'skills', 'skill-name')
        join_mock.assert_called_once_with('cwd', 'skills', 'skill-name')
        exists_mock.assert_called_once_with('some-path')

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=False)
    def test__get_item_source_path_not_exists(self, exists_mock, join_mock):
        """Test for _get_item_source_path item already exists."""
        with self.assertRaises(ClickException):
            _get_item_source_path('cwd', 'skills', 'skill-name')


@mock.patch('aea.cli.registry.push.get_packages_path', return_value='packages')
@mock.patch('aea.cli.registry.push.os.path.join', return_value='some-path')
class GetItemTargetPathTestCase(TestCase):
    """Test case for _get_item_target_path method."""

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=False)
    def test__get_item_target_path_positive(
        self, exists_mock, join_mock, get_packages_path_mock
    ):
        """Test for _get_item_source_path positive result."""
        _get_item_target_path('skills', 'skill-name')
        join_mock.assert_called_once_with('packages', 'skills', 'skill-name')
        exists_mock.assert_called_once_with('some-path')

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=True)
    def test__get_item_target_path_already_exists(
        self, exists_mock, join_mock, get_packages_path_mock
    ):
        """Test for _get_item_target_path item already exists."""
        with self.assertRaises(ClickException):
            _get_item_target_path('skills', 'skill-name')

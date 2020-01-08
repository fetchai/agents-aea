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
from click.testing import CliRunner

from aea.cli import cli
from aea.cli.registry.push import (
    push_item,
    _remove_pycache,
    save_item_locally,
)
from aea.configurations.base import PublicId
from tests.conftest import CLI_LOG_OPTION


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


@mock.patch('aea.cli.registry.push.copytree')
@mock.patch('aea.cli.registry.push.os.getcwd', return_value='cwd')
class SaveItemLocallyTestCase(TestCase):
    """Test case for save_item_locally method."""

    @mock.patch(
        'aea.cli.registry.push.get_item_target_path', return_value='target'
    )
    @mock.patch(
        'aea.cli.registry.push.get_item_source_path', return_value='source'
    )
    @mock.patch(
        'aea.cli.registry.push.load_yaml', return_value={"author": "fetchai", "version": "0.1.0", "name": "skill_name"}
    )
    def test_save_item_locally_positive(
        self,
        load_yaml_mock,
        get_item_source_path_mock,
        get_item_target_path_mock,
        getcwd_mock,
        copy_tree_mock,
    ):
        """Test for save_item_locally positive result."""
        item_type = 'skill'
        item_id = PublicId.from_string('fetchai/skill_name:0.1.0')
        save_item_locally(item_type, item_id, 'packages_path')
        get_item_source_path_mock.assert_called_once_with(
            'cwd', 'skills', item_id.name
        )
        get_item_target_path_mock.assert_called_once_with(
            'skills', item_id.name, 'packages_path'
        )
        getcwd_mock.assert_called_once()
        copy_tree_mock.assert_called_once_with('source', 'target')


@mock.patch('aea.cli.registry.push.copytree')
@mock.patch('aea.cli.registry.push.os.getcwd', return_value='cwd')
class SaveItemLocallyFailsTestCase(TestCase):
    """Test case for save_item_locally method."""

    @mock.patch(
        'aea.cli.registry.push.get_item_target_path', return_value='target'
    )
    @mock.patch(
        'aea.cli.registry.push.get_item_source_path', return_value='source'
    )
    @mock.patch(
        'aea.cli.registry.push.load_yaml', return_value={"author": "fetchai", "version": "0.1.0", "name": "skill_name"}
    )
    def test_save_item_locally_positive(
        self,
        load_yaml_mock,
        get_item_source_path_mock,
        get_item_target_path_mock,
        getcwd_mock,
        copy_tree_mock,
    ):
        """Test for save_item_locally  - item not found."""
        with self.assertRaises(ClickException):
            item_type = 'skill'
            item_id = PublicId.from_string('non_existing_author/skill_name:0.1.0')
            save_item_locally(item_type, item_id, 'packages_path')


class TestPushLocalFailsArgumentNotPublicId:
    """Test the case when we try a local push with a non public id."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.runner = CliRunner()
        cls.result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "push", "--local", "connection", "oef"],
                                       standalone_mode=False)

    def test_exit_code_2(self):
        """Test the exit code is 2 (i.e. bad usage)."""
        assert self.result.exit_code == 1
        assert self.result.exception.exit_code == 2

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""

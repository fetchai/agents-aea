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
"""Test module for Registry publish methods."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli.registry.publish import (
    publish_agent, _load_agent_config, save_agent_locally
)


@mock.patch('aea.cli.registry.utils._rm_tarfiles')
@mock.patch('aea.cli.registry.publish.os.getcwd', return_value='cwd')
@mock.patch('aea.cli.registry.publish._compress')
@mock.patch(
    'aea.cli.registry.publish._load_agent_config',
    return_value={
        'agent_name': 'agent-name',
        'description': 'some-description',
        'version': 'some-version'
    }
)
@mock.patch(
    'aea.cli.registry.publish.request_api',
    return_value={'public_id': 'public-id'}
)
class PublishAgentTestCase(TestCase):
    """Test case for publish_agent method."""

    def test_push_item_positive(
        self,
        request_api_mock,
        _load_agent_config_mock,
        _compress_mock,
        getcwd_mock,
        _rm_tarfiles_mock
    ):
        """Test for publish_agent positive result."""
        publish_agent()
        request_api_mock.assert_called_once_with(
            'POST',
            '/agents/create',
            data={
                'name': 'agent-name',
                'description': 'some-description',
                'version': 'some-version',

            },
            auth=True,
            filepath='cwd/agent-name.tar.gz'
        )


@mock.patch('aea.cli.registry.publish.load_yaml')
class LoadAgentConfigTestCase(TestCase):
    """Test case for _load_agent_config method."""

    @mock.patch('aea.cli.registry.publish.os.path.exists', return_value=True)
    def test__load_agent_config_positive(
        self, path_exists_mock, load_yaml_mock
    ):
        """Test for _load_agent_config positive result."""
        _load_agent_config('path')
        load_yaml_mock.assert_called_once_with('path')

    @mock.patch('aea.cli.registry.publish.os.path.exists', return_value=False)
    def test__load_agent_config_path_not_exists(
        self, path_exists_mock, load_yaml_mock
    ):
        """Test for _load_agent_config path not exists."""
        with self.assertRaises(ClickException):
            _load_agent_config('path')

        load_yaml_mock.assert_not_called()


@mock.patch('aea.cli.registry.publish.copyfile')
@mock.patch('aea.cli.registry.publish.os.makedirs')
@mock.patch('aea.cli.registry.publish.os.path.exists', return_value=False)
@mock.patch(
    'aea.cli.registry.publish.get_item_target_path',
    return_value='target-dir'
)
@mock.patch(
    'aea.cli.registry.publish._load_agent_config',
    return_value={'agent_name': 'agent-name'}
)
@mock.patch('aea.cli.registry.publish.os.path.join', return_value='joined-path')
@mock.patch('aea.cli.registry.publish.os.getcwd', return_value='cwd')
class SaveAgentLocallyTestCase(TestCase):
    """Test case for save_agent_locally method."""

    def test_save_agent_locally_positive(
        self,
        getcwd_mock,
        path_join_mock,
        _load_agent_config_mock,
        get_item_target_path_mock,
        path_exists_mock,
        makedirs_mock,
        copyfile_mock
    ):
        """Test for save_agent_locally positive result."""
        save_agent_locally()
        makedirs_mock.assert_called_once_with('target-dir', exist_ok=True)
        copyfile_mock.assert_called_once_with('joined-path', 'joined-path')

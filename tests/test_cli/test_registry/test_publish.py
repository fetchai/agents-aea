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

from aea.cli.registry.publish import publish_agent


@mock.patch('aea.cli.registry.utils._rm_tarfiles')
@mock.patch('aea.cli.registry.publish.os.getcwd', return_value='cwd')
@mock.patch('aea.cli.registry.publish._compress')
@mock.patch(
    'aea.cli.registry.publish.load_yaml',
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

    @mock.patch('aea.cli.registry.publish.os.path.exists', return_value=True)
    def test_push_item_positive(
        self,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock
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

    @mock.patch('aea.cli.registry.push.os.path.exists', return_value=False)
    def test_publish_agent_config_not_found(
        self,
        path_exists_mock,
        request_api_mock,
        load_yaml_mock,
        compress_mock,
        getcwd_mock,
        rm_tarfiles_mock
    ):
        """Test for publish_agent - config not found."""
        with self.assertRaises(ClickException):
            publish_agent()

        request_api_mock.assert_not_called()

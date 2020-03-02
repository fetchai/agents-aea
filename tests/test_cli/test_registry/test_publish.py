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

from aea.cli.registry.publish import _compress, _load_agent_config, publish_agent

from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("aea.cli.registry.publish.check_is_author_logged_in")
@mock.patch("aea.cli.registry.utils._rm_tarfiles")
@mock.patch("aea.cli.registry.publish.os.getcwd", return_value="cwd")
@mock.patch("aea.cli.registry.publish._compress")
@mock.patch(
    "aea.cli.registry.publish._load_agent_config",
    return_value={
        "agent_name": "agent-name",
        "description": "some-description",
        "version": "some-version",
        "author": "some-author",
        "connections": [],
        "contracts": [],
        "protocols": [],
        "skills": [],
    },
)
@mock.patch(
    "aea.cli.registry.publish.request_api", return_value={"public_id": "public-id"}
)
class PublishAgentTestCase(TestCase):
    """Test case for publish_agent method."""

    def test_push_item_positive(
        self,
        request_api_mock,
        _load_agent_config_mock,
        _compress_mock,
        getcwd_mock,
        _rm_tarfiles_mock,
        check_is_author_logged_in_mock,
    ):
        """Test for publish_agent positive result."""
        publish_agent(ContextMock())
        request_api_mock.assert_called_once_with(
            "POST",
            "/agents/create",
            data={
                "name": "agent-name",
                "description": "some-description",
                "version": "some-version",
                "connections": [],
                "contracts": [],
                "protocols": [],
                "skills": [],
            },
            is_auth=True,
            filepath="cwd/agent-name.tar.gz",
        )


@mock.patch("aea.cli.registry.publish.load_yaml")
class LoadAgentConfigTestCase(TestCase):
    """Test case for _load_agent_config method."""

    @mock.patch("aea.cli.registry.publish.os.path.exists", return_value=True)
    def test__load_agent_config_positive(self, path_exists_mock, load_yaml_mock):
        """Test for _load_agent_config positive result."""
        _load_agent_config("path")
        load_yaml_mock.assert_called_once_with("path")

    @mock.patch("aea.cli.registry.publish.os.path.exists", return_value=False)
    def test__load_agent_config_path_not_exists(self, path_exists_mock, load_yaml_mock):
        """Test for _load_agent_config path not exists."""
        with self.assertRaises(ClickException):
            _load_agent_config("path")

        load_yaml_mock.assert_not_called()


@mock.patch("aea.cli.registry.publish.tarfile")
class CompressTestCase(TestCase):
    """Test case for _compress method."""

    def test__compress_positive(self, tarfile_mock):
        """Test for _compress positive result."""
        tar_obj_mock = mock.MagicMock()
        open_mock = mock.MagicMock(return_value=tar_obj_mock)
        tarfile_mock.open = open_mock

        _compress("output_filename", "file1", "file2")
        open_mock.assert_called_once_with("output_filename", "w:gz")

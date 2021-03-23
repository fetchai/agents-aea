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
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import mock_open

from aea.cli.registry.publish import _compress, publish_agent
from aea.test_tools.test_cases import AEATestCase

from tests.conftest import CUR_PATH
from tests.test_cli.tools_for_testing import ContextMock


@mock.patch("builtins.open", mock_open(read_data="test"))
@mock.patch("aea.cli.registry.publish.shutil.copy")
@mock.patch("aea.cli.registry.publish.try_to_load_agent_config")
@mock.patch("aea.cli.registry.publish.check_is_author_logged_in")
@mock.patch("aea.cli.registry.utils._rm_tarfiles")
@mock.patch("aea.cli.registry.publish.os.getcwd", return_value="cwd")
@mock.patch("aea.cli.registry.publish._compress")
@mock.patch(
    "aea.cli.registry.publish.request_api", return_value={"public_id": "public-id"}
)
class PublishAgentTestCase(TestCase):
    """Test case for publish_agent method."""

    @mock.patch("aea.cli.registry.publish.is_readme_present", return_value=True)
    def test_publish_agent_positive(
        self, is_readme_present_mock, request_api_mock, *mocks
    ):
        """Test for publish_agent positive result."""
        description = "Some description."
        version = "0.1.0"
        context_mock = ContextMock(description=description, version=version)
        publish_agent(context_mock)
        request_api_mock.assert_called_once_with(
            "POST",
            "/agents/create",
            data={
                "name": "agent_name",
                "description": description,
                "version": version,
                "connections": [],
                "contracts": [],
                "protocols": [],
                "skills": [],
            },
            is_auth=True,
            files={"file": mock.ANY, "readme": mock.ANY},
        )

    @mock.patch("aea.cli.registry.publish.is_readme_present", return_value=False)
    def test_publish_agent_without_readme_positive(
        self, is_readme_present_mock, request_api_mock, *mocks
    ):
        """Test for publish_agent without readme positive result."""
        description = "Some description."
        version = "0.1.0"
        context_mock = ContextMock(description=description, version=version)
        publish_agent(context_mock)
        request_api_mock.assert_called_once_with(
            "POST",
            "/agents/create",
            data={
                "name": "agent_name",
                "description": description,
                "version": version,
                "connections": [],
                "contracts": [],
                "protocols": [],
                "skills": [],
            },
            is_auth=True,
            files={"file": mock.ANY},
        )


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


@mock.patch("aea.cli.registry.publish.request_api", side_effect=ValueError("expected"))
class PublishAgentCleanupOnFailTestCase(AEATestCase):
    """Test case for publish_agent method."""

    path_to_aea = Path(CUR_PATH) / "data" / "dummy_aea"

    def test_publish_agent_fails(self, *mocks):
        """Test for publish_agent positive result."""
        description = "Some description."
        version = "0.1.0"
        context_mock = ContextMock(description=description, version=version)
        context_mock.cwd = "."
        publish_agent(context_mock)
